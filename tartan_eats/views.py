from calendar import prmonth
import json
import re
from pickletools import read_uint1

import requests
# should change if we use Google authenticate login logout
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
# should change if we use Google authenticate login logout
from django.contrib.auth.models import User
# chuchu
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from tartan_eats.forms import (CuisineForm, CustomerEditForm,
                               CustomerRegisterForm, DriverRegisterForm,
                               RestaurantRegisterForm, RestaurantEditForm, OrderForm)
from tartan_eats.models import (Cuisine, Customer, Delivery, Driver, Order,
                                Order_Cuisine, Restaurant, Role)

google_map_key = 'AIzaSyDYWsR4-KO2YyJ-vDrb-V6m8Ah-f6_fmZo'



def customer_home(request):
    if request.method == 'GET':
        return render(request, 'tartan_eats/customer-home.html', {'restaurants': Restaurant.objects.all()})

# ------------- ke -------------------------
@login_required
def driver_home(request):
    context = {}
    if request.method == 'GET':
        context['form'] = DriverRegisterForm()
        return render(request, 'tartan_eats/driver-profile.html', {"form": DriverRegisterForm(), "message": ""})
    form = DriverRegisterForm(request.POST, request.FILES)
    print(request.POST)
    print(request.FILES)
    context['form'] = form
    context['message'] = ""
    if not form.is_valid():
        print("invalid")
        return render(request, 'tartan_eats/driver-profile.html', context)
    # updated_driver = Driver.objects.get(user=request.user)
    updated_driver = Driver.objects.select_for_update().get(user=request.user)
    updated_driver.firstname = form.cleaned_data['firstname']
    updated_driver.lastname = form.cleaned_data['lastname']
    updated_driver.email = form.cleaned_data['email']
    updated_driver.phone = form.cleaned_data['phone']
    pic = form.cleaned_data['driver_picture']
    print(pic)
    if pic is not None:
        updated_driver.driver_picture = form.cleaned_data['driver_picture']
        updated_driver.content_type = form.cleaned_data['driver_picture'].content_type
    updated_driver.save()
    context['form'] = DriverRegisterForm()
    context['message'] = ""
    return render(request, 'tartan_eats/driver-profile.html', context)

@login_required
def get_driver_picture(request):
    driver = request.user.driver
    print('Picture #{} fetched from db: {} (type={})'.format(id, driver.driver_picture, type(driver.driver_picture)))
    if not driver.driver_picture:
        raise Http404
    return HttpResponse(driver.driver_picture, driver.content_type)


@login_required
def driver_change_delivery(request):
    delivery = Driver.objects.get(user_id=request.user.id).delivery_set.filter(delivery_status='in-delivery').first()
    delivery.delivery_status = "completed"
    delivery.save()
    order = delivery.order
    order.order_status = "completed"
    order.save()
    driver = request.user.driver
    driver.avalable_status = "available"
    driver.save()
    return redirect(reverse('driver-order-completed'))

@login_required
def driver_order_indelivery(request):
    context = {}
    delivery = Driver.objects.get(user_id=request.user.id).delivery_set.filter(delivery_status='in-delivery').first()
    if delivery is None:
        context['error'] = 'You currently have no order in delivery'
        return render(request, 'tartan_eats/driver-order-indelivery.html', context)
    if request.method == 'GET':
        context['delivery'] = delivery
        order = delivery.order
        customer_address = order.real_address1 + " " + order.real_address2
        route_information_list = delivery.route_information.split('|')
        context['realtime_position_id'] = delivery.realtime_position
        context['customer_full_address'] = customer_address
        context['key'] = google_map_key
        context['update_mode'] = 'false'
        context['cnt'] = 0
        try:
            context['destination_id'] = route_information_list[3]
            return render(request, 'tartan_eats/driver-order-indelivery.html', context)
        except Exception:
            context['destination_id'] = get_place_id(customer_address)
            return render(request, 'tartan_eats/driver-order-indelivery.html', context)

# update driver location
# cnt represent the number of times update button was clicked
@login_required
def driver_update_location(request):
    delivery = Driver.objects.get(user_id=request.user.id).delivery_set.filter(delivery_status='in-delivery').first()
    context = {}
    context['delivery'] = delivery
    order = delivery.order
    customer_address = order.real_address1 + " " + order.real_address2
    context['customer_full_address'] = customer_address
    route_information_list = delivery.route_information.split("|")
    context['key'] = google_map_key
    try:
        context['destination_id'] = route_information_list[3]
        if delivery.cnt == 0:  # no update yet
            delivery.realtime_position = route_information_list[1]  # id1
            delivery.cnt = 1
        elif delivery.cnt == 1:
            delivery.realtime_position = route_information_list[2]  # id2
            delivery.cnt = 2
        elif delivery.cnt == 2:
            delivery.realtime_position = route_information_list[3]  # destination_id
            delivery.cnt = 3
        else:
            delivery.cnt = 4
        delivery.save()
        context['realtime_position_id'] = delivery.realtime_position
        context['cnt'] = delivery.cnt
        return render(request, 'tartan_eats/driver-order-indelivery.html', context)
    except Exception:
        realtime_position_id = get_place_id(order.restaurant.restaurant_address)
        context['cnt'] = 3
        context['realtime_position_id'] = realtime_position_id
        context['destination_id'] = get_place_id(customer_address)
        delivery.cnt = 3
        delivery.realtime_position = realtime_position_id
        delivery.save()
        return render(request, 'tartan_eats/driver-order-indelivery.html', context)
def driver_change_status(request):
    # change status
    driver = request.user.driver
    print("name: " + driver.firstname)
    print("status: " + driver.avalable_status)
    if driver.avalable_status == "available":
        driver.avalable_status = "unavailable"
        driver.save()
    else:
        if driver.delivery_set.exists() & driver.delivery_set.filter(delivery_status='in-delivery').exists():
            return render(request, 'tartan_eats/driver-profile.html', {"form": DriverRegisterForm(),
                                                                       "message": "Cannot change to Available because you have an order in delivery"})
        else:
            driver.avalable_status = "available"
            driver.save()
    return redirect(reverse('driver-home'))

@login_required
def driver_order_completed(request):
    context = {}
    deliveries = Driver.objects.get(user_id=request.user.id).delivery_set.filter(delivery_status='completed')
    if request.method == 'GET':
        context['deliveries'] = deliveries
        return render(request, 'tartan_eats/driver-order-completed.html', context)


# --------------- ke ------------

def home_action(request):
    if not request.user.id:
        return redirect(reverse('login'))
    if not hasattr(request.user, 'role'):
        print(hasattr(request.user, 'role'))
        return render(request, 'tartan_eats/register.html')
    if request.method == 'GET':
        if (request.user.role.type == 'customer'):
            return redirect(reverse('customer-home'))
        if (request.user.role.type == 'restaurant'):
            return redirect(reverse('restaurant-home'))
        if (request.user.role.type == 'driver'):
            return redirect(reverse('driver-home'))


def login_action(request):
    if request.user.id:
        return redirect(reverse('home'))
    context = {}
    if request.method == 'GET':
        return render(request, 'tartan_eats/login.html', context)

@login_required
def register_customer(request):
    # if the user has been registered. redirect to home.
    # if request.user.customer:
    #    return redirect(reverse('home'))
    context = {}
    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = CustomerRegisterForm()
        return render(request, 'tartan_eats/register-customer.html', context)
    form = CustomerRegisterForm(request.POST, request.FILES)
    context['form'] = form
    # Validates the form.
    if not form.is_valid():
        return render(request, 'tartan_eats/register-customer.html', context)
    if(form.cleaned_data['customer_picture']):
        customer = Customer(user = request.user, firstname = form.cleaned_data['firstname'],
                            lastname = form.cleaned_data['lastname'],
                            email = form.cleaned_data['email'],
                            phone = form.cleaned_data['phone'],
                            address1=form.cleaned_data['address1'],
                            address2= form.cleaned_data['address2'],
                            zipcode = form.cleaned_data['zipcode'],
                            city = form.cleaned_data['city'],
                            customer_picture = form.cleaned_data['customer_picture'],
                            content_type = form.cleaned_data['customer_picture'].content_type)
    else:
         customer = Customer(user = request.user, firstname = form.cleaned_data['firstname'],
                            lastname = form.cleaned_data['lastname'],
                            email = form.cleaned_data['email'],
                            phone = form.cleaned_data['phone'],
                            address1=form.cleaned_data['address1'],
                            address2= form.cleaned_data['address2'],
                            zipcode = form.cleaned_data['zipcode'],
                            city = form.cleaned_data['city'],
                            customer_picture = form.cleaned_data['customer_picture'])

    customer.save()
    role = Role(user=request.user, type='customer')
    role.save()
    return redirect(reverse('home'))

@login_required
def register_restaurant(request):
    context = {}
    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = RestaurantRegisterForm()
        return render(request, 'tartan_eats/register-restaurant.html', context)

    form = RestaurantRegisterForm(request.POST, request.FILES)
    context['form'] = form

    if not form.is_valid():
        return render(request, 'tartan_eats/register-restaurant.html', context)
    if (form.cleaned_data['restaurant_picture']):
        new_restaurant = Restaurant(
            user=request.user,
            restaurant_name=form.cleaned_data['restaurant_name'],
            email=form.cleaned_data['email'],
            phone=form.cleaned_data['phone'],
            restaurant_address=form.cleaned_data['restaurant_address'],
            restaurant_description=form.cleaned_data['restaurant_description'],
            delivery_fee=form.cleaned_data['delivery_fee'],
            # venmo_account=form.cleaned_data['venmo_account'],
            restaurant_picture=form.cleaned_data['restaurant_picture'],
            content_type=form.cleaned_data['restaurant_picture'].content_type
        )
    else:
        new_restaurant = Restaurant(
            user=request.user,
            restaurant_name=form.cleaned_data['restaurant_name'],
            email=form.cleaned_data['email'],
            phone=form.cleaned_data['phone'],
            restaurant_address=form.cleaned_data['restaurant_address'],
            restaurant_description=form.cleaned_data['restaurant_description'],
            delivery_fee=form.cleaned_data['delivery_fee'],
            # venmo_account=form.cleaned_data['venmo_account'],
            restaurant_picture=form.cleaned_data['restaurant_picture']
        )

    new_restaurant.save()
    role = Role(user=request.user, type='restaurant')
    role.save()
    return redirect(reverse('restaurant-home'))

@login_required
def register_driver(request):
    context = {}
    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
        context['form'] = DriverRegisterForm()
        return render(request, 'tartan_eats/register-driver.html', context)
    form = DriverRegisterForm(request.POST, request.FILES)
    context['form'] = form
    # Validates the form.
    if not form.is_valid():
        return render(request, 'tartan_eats/register-driver.html', context)
    if (form.cleaned_data['driver_picture']):
        driver = Driver(user=request.user, firstname=form.cleaned_data['firstname'],
                        lastname=form.cleaned_data['lastname'], email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'], avalable_status="available",
                        driver_picture=form.cleaned_data['driver_picture'],
                        content_type=form.cleaned_data['driver_picture'].content_type
                        )
    else:
        driver = Driver(user=request.user, firstname=form.cleaned_data['firstname'],
                        lastname=form.cleaned_data['lastname'], email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'], avalable_status="available",
                        driver_picture=form.cleaned_data['driver_picture']
                        )

    driver.save()
    role = Role(user=request.user, type='driver')
    role.save()
    return redirect(reverse('driver-home'))


# -------------- customer side---------chu----------------------#
@login_required
def single_restaurant(request, restaurant_id):
    # require login
    if not request.user.id:
        return redirect(reverse('login'))
    # if user has not registered. redirect to register
    if not hasattr(request.user, 'role'):
        print(hasattr(request.user, 'role'))
        return render(request, 'tartan_eats/register.html')
    restaurant = Restaurant.objects.get(user_id=restaurant_id)
    cuisines = Cuisine.objects.filter(restaurant=restaurant_id, online=True)
    context = {'restaurant': restaurant, 'cuisines': cuisines}

    # also update cart each time visit, should only have one or non order_in_cart
    # check if there is order in cart
    orders_in_cart = get_orders(request.user.id, restaurant_id, "adding")
    if orders_in_cart:
        order_in_cart = orders_in_cart[0]
        all_cuisine_in_cart = Order_Cuisine.objects.filter(order=order_in_cart)
        # check if the cuisine in cart is online = true
        all_cuisine_in_cart = filter_offline_order(request, all_cuisine_in_cart, order_in_cart)
        context['all_cuisine_in_cart'] = all_cuisine_in_cart
        context['order'] = order_in_cart
    # if not, do not send any context to the html #TODO may need to check bugs
    if request.method == 'GET':
        return render(request, 'tartan_eats/customer-single-restaurant.html', context)


def filter_offline_order(request, all_cuisine_in_cart_before_filter, order_in_cart):
    for order_cuisine_in_cart in all_cuisine_in_cart_before_filter:
        cuisine_id = order_cuisine_in_cart.cuisine_id
        cuisine = Cuisine.objects.get(id=cuisine_id)
        if cuisine.online == False:
            # delete from cart and update subtotal
            delete_from_cart(request, cuisine_id)
    # re get the all order_cuisine in cart after delete
    all_cuisine_in_cart = Order_Cuisine.objects.filter(order=order_in_cart)
    return all_cuisine_in_cart


def add_to_cart(request, cuisine_id):
    # require login
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=403)
    cuisine_to_add = get_object_or_404(Cuisine, id=cuisine_id)
    restaurant_id = cuisine_to_add.restaurant.user.id
    restaurant = Restaurant.objects.get(user_id=restaurant_id)
    cuisines = Cuisine.objects.filter(restaurant=restaurant_id)

    # add order and cuisine to db . filter out the order of "adding stage"
    orders_in_cart = get_orders(request.user.id, restaurant_id, "adding")
    print("order_in_cart : " + str(orders_in_cart))
    # if the customer does not have order of adding status, create a new order
    if not orders_in_cart:
        new_order = Order(customer=User.objects.get(id=request.user.id).customer,
                          restaurant=User.objects.get(id=restaurant_id).restaurant,
                          order_status="adding",
                          order_time=timezone.now(),
                          real_first_name = User.objects.get(id=request.user.id).customer.firstname,
                          real_last_name = User.objects.get(id=request.user.id).customer.lastname,
                          real_email = User.objects.get(id=request.user.id).customer.email,
                          real_phone = User.objects.get(id=request.user.id).customer.phone,
                          real_address1 = User.objects.get(id=request.user.id).customer.address1,
                          real_address2 = User.objects.get(id=request.user.id).customer.address2
                          )
        new_order.save()

    # if the customer has order in adding status, check order_cuisine then add cuisine in this order
    order_in_cart = get_orders(request.user.id, restaurant_id, "adding")[0]  # TODO   orders_in_cart[0]
    cuisine_in_cart = Order_Cuisine.objects.filter(order=order_in_cart, cuisine=cuisine_to_add)
    print("cuisine_in_cart : " + str(cuisine_in_cart))
    # if order does not have this cuisine, add this cuisine
    if not cuisine_in_cart:
        new_order_cuisine = Order_Cuisine(order=order_in_cart, cuisine=cuisine_to_add, item_quantity=1)
        new_order_cuisine.save()
    # if in this order, there is already this cuisine, add the quantity by 1
    else:
        order_cuisine = cuisine_in_cart[0]
        # update quantity +1
        order_cuisine.item_quantity = order_cuisine.item_quantity + 1
        order_cuisine.save()  # ?? why white color

    # calculate subtotal for this order and update order and subtotal in model
    subtotal, all_cuisine_in_cart = get_cuisine_and_cal_subtotal(request.user.id, restaurant_id, "adding")
    order_in_cart = get_orders(request.user.id, restaurant_id, "adding")[0]  # needs to be get again. cannot be deleted
    # show all the cuisines in cart in the shopping cart
    context = {'restaurant': restaurant, 'cuisines': cuisines,
               'all_cuisine_in_cart': all_cuisine_in_cart, 'order': order_in_cart}
    return get_cart_list_json_dumps(request, restaurant.user.id)


# helper method for add to cart function. get order object by its userid, restaurant id and order status.

def get_orders(user_id, restaurant_id, order_status):
    order_in_cart = Order.objects.filter(customer=User.objects.get(id=user_id).customer,
                                         restaurant=User.objects.get(id=restaurant_id).restaurant,
                                         order_status=order_status)
    return order_in_cart


# helper method for add-to cart to calculate the subototal of one order in one restaurant.

def get_cuisine_and_cal_subtotal(user_id, restaurant_id, order_status):
    order = get_orders(user_id, restaurant_id, order_status)
    # if order does not exist
    subtotal = 0
    all_cuisine_in_cart = []
    # if order exists.
    if order:
        order = order[0]
        all_cuisine_in_cart = Order_Cuisine.objects.filter(order=order)
        print("all_cuisine_in_cart : " + str(all_cuisine_in_cart))

        for cuisine_in_cart in all_cuisine_in_cart:
            subtotal = subtotal + cuisine_in_cart.item_quantity * cuisine_in_cart.cuisine.price

        order.subtotal = subtotal
        order.save()
    return subtotal, all_cuisine_in_cart



#  re-calculate subtotal and save the subtotal to db
# delete the cuisine in order_cuisine
def delete_from_cart(request, cuisine_id):
    # require login
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=403)
    cuisine_to_delete = Cuisine.objects.get(id=cuisine_id)
    # the order should be of this restaurant and this user
    restaurant = cuisine_to_delete.restaurant
    cuisines = Cuisine.objects.filter(restaurant=restaurant)
    # context = {'restaurant':restaurant,'cuisines':cuisines}
    context = {}
    # if request.method != 'POST':
    #     #context['error'] = 'Deletes must be done using the POST method'
    #     return render(request, 'tartan_eats/customer-single-restaurant.html', context)
    # Deletes the item if present in the order_cuisine database.
    try:
        # 1. get order_cuisine to delete
        # there should only be one order that is from this customer and in this restaurant
        order = get_orders(request.user.id, restaurant.user.id, "adding")[0]
        order_cuisine_to_delete = Order_Cuisine.objects.get(cuisine=cuisine_id, order=order)
        order_cuisine_to_delete.delete()
        print("___________deleted one item" + str(order_cuisine_to_delete))

        # 2. recalculate subtotal
        subtotal, all_cuisine_in_car = get_cuisine_and_cal_subtotal(request.user.id, restaurant.user.id, "adding")

        # return json format of all the cart content in this restaurant
        return get_cart_list_json_dumps(request, restaurant.user.id)
    except ObjectDoesNotExist:
        context['error'] = 'The item did not exist in the shopping cart.'
        return render(request, 'tartan_eats/customer-single-restaurant.html', context)


# show json list of the shopping cart, for ajax use.
def get_cart_list_json_dumps(request, restaurant_id):
    # require login
    if not request.user.id:
        return _my_json_error_response("You must be logged in to do this operation", status=403)
    subtotal, all_cuisine_in_cart = get_cuisine_and_cal_subtotal(request.user.id, restaurant_id, "adding")
    response_data = []
    # TODO what if all_Cuisine_in_Cart is empty
    order_id = -1
    if all_cuisine_in_cart:
        order_id = all_cuisine_in_cart[0].order_id
        response_data.append({'order_id': order_id})
    for cuisine_in_cart in all_cuisine_in_cart:
        cuisine = Cuisine.objects.get(id=cuisine_in_cart.cuisine_id)
        all_item = {
            'id': cuisine_in_cart.id,
            'cuisine_id': cuisine_in_cart.cuisine_id,
            'cuisine_name': cuisine.cuisine_name,
            'price': cuisine.price,
            'item_quantity': cuisine_in_cart.item_quantity
        }
        response_data.append(all_item)

    all_subtotal = {'subtotal': subtotal}
    response_data.append(all_subtotal)
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


def _my_json_error_response(message, status=200):
    # You can create your JSON by constructing the string representation yourself (or just use json.dumps)
    response_json = '{ "error": "' + message + '" }'
    return HttpResponse(response_json, content_type='application/json', status=status)


# -------------- customer side -- cart part -- end ---------chu----------------------#

def register_action(request):
    # if user has already registered. redirect to home
    if hasattr(request.user, 'role'):
        print(hasattr(request.user, 'role'))
        return redirect(reverse('login'))
    if request.method == 'GET':
        return render(request, 'tartan_eats/register.html')

@login_required
def restaurant_profile(request):
    if request.method == 'GET':
        # context = {
        #     'profile': request.user.profile,
        #     'form' : RestaurantProfileForm(initial={'bio': request.user.profile.bio})
        # }
        return render(request, 'tartan_eats/restaurant-profile.html')


# cuisine_id is optional
@login_required
def restaurant_home(request, cuisine_id=None):
    context = {
        'restaurant': request.user.restaurant,
        'profile_form': RestaurantEditForm(initial={
            'restaurant_name': request.user.restaurant.restaurant_name,
            'restaurant_address': request.user.restaurant.restaurant_address,
            'restaurant_description': request.user.restaurant.restaurant_description,
            'delivery_fee': request.user.restaurant.delivery_fee,
            'phone': request.user.restaurant.phone,
            'email': request.user.restaurant.email,
            'restaurant_picture': request.user.restaurant.restaurant_picture
        }),
        'cuisine_form': CuisineForm({
            'cuisine_name': "",
            'cuisine_description': "",
            'cuisine_picture': "",
            'price': ""
        }),
        'cuisine_list': Cuisine.objects.filter(restaurant=request.user.restaurant, online=True).all(),
        'offline_cuisine_list': Cuisine.objects.filter(restaurant=request.user.restaurant,
                                                       online=False).all()
    }
    if request.method == 'GET':
        return render(request, 'tartan_eats/restaurant-profile.html', context)
    if request.method == 'POST':
        # select for update
        original_restaurant = Restaurant.objects.select_for_update().get(user_id=request.user.id)
        if 'profile_button' in request.POST:
            print("______________________editing restaurant form!!!!!!! ______________________")
            edit_profile_form = RestaurantEditForm(request.POST, request.FILES, instance=original_restaurant)
            # must call isValid to user clean data
            if not edit_profile_form.is_valid():  # return unchanged profile and form
                context['profile'] = request.user.restaurant
                context['profile_form'] = edit_profile_form
                return render(request, 'tartan_eats/restaurant-profile.html', context)
            restaurant_name = edit_profile_form.cleaned_data['restaurant_name']
            restaurant_address = edit_profile_form.cleaned_data['restaurant_address']
            restaurant_description = edit_profile_form.cleaned_data['restaurant_description']
            print("new description: " + restaurant_description)
            delivery_fee = edit_profile_form.cleaned_data['delivery_fee']
            phone = edit_profile_form.cleaned_data['phone']
            email = edit_profile_form.cleaned_data['email']
            # venmo_account = edit_profile_form.cleaned_data['venmo_account']
            pic = edit_profile_form.cleaned_data['restaurant_picture']
            print(pic)
            if pic is not None:
                print('Uploaded picture: {} (type={})'.format(pic, type(pic)))
                original_restaurant.restaurant_picture = pic
                try:
                    original_restaurant.content_type = edit_profile_form.cleaned_data['restaurant_picture'].content_type
                except AttributeError:
                    print("type")
                    print(type(pic))
            original_restaurant.restaurant_name = restaurant_name
            original_restaurant.restaurant_address = restaurant_address
            original_restaurant.restaurant_description = restaurant_description
            original_restaurant.delivery_fee = delivery_fee
            original_restaurant.phone = phone
            original_restaurant.email = email
            # original_restaurant.venmo_account = venmo_account
            original_restaurant.save()  # save new profile
        if 'add-button' in request.POST:
            cuisine_form = CuisineForm(request.POST, request.FILES)
            if not cuisine_form.is_valid():  # return unchanged profile and
                # form
                context['error'] = "The number of price should be positive. Please try again."
                context['cuisine_form'] = cuisine_form
                context['profile'] = request.user.restaurant
                print("invalid form")
                return render(request, 'tartan_eats/restaurant-profile.html', context)
            cuisine_name = cuisine_form.cleaned_data['cuisine_name']
            cuisine_description = cuisine_form.cleaned_data['cuisine_description']
            price = cuisine_form.cleaned_data['price']
            cuisine_picture = cuisine_form.cleaned_data['cuisine_picture']
            # print("____________________cuisine post")
            print(request.POST)
            print(request.FILES)
            if cuisine_picture is not None:
                # print('______________Uploaded picture: {} (type={})'.format(cuisine_picture, type(cuisine_picture)))
                new_cuisine = Cuisine(cuisine_name=cuisine_name, cuisine_description=cuisine_description,
                                      price=price,
                                      content_type=cuisine_form.cleaned_data['cuisine_picture'].content_type,
                                      cuisine_picture=cuisine_picture, restaurant=original_restaurant)
                new_cuisine.save()
                # print("________________________new cuisine created! " + str(new_cuisine))
            else:
                # print('______________Uploaded picture: {} (type={})'.format(cuisine_picture, type(cuisine_picture)))
                new_cuisine = Cuisine(cuisine_name=cuisine_name, cuisine_description=cuisine_description,
                                      price=price, restaurant=original_restaurant
                                      )
                new_cuisine.save()
                # print("_________________________________error: cuisine picture is none")
        # set cuisine online = false
        if request.method == 'POST' and 'offline_button' in request.POST:
            original_restaurant = request.user.restaurant
            cuisine_to_remove = Cuisine.objects.get(id=cuisine_id)
            cuisine_to_remove.online = False
            cuisine_to_remove.save()
        if request.method == 'POST' and 'online_button' in request.POST:
            original_restaurant = request.user.restaurant
            cuisine_to_remove = Cuisine.objects.get(id=cuisine_id)
            cuisine_to_remove.online = True
            cuisine_to_remove.save()
        # same action for both forms
        context['cuisine_list'] = Cuisine.objects.filter(restaurant=original_restaurant, online=True).all()
        context['offline_cuisine_list'] = Cuisine.objects.filter(restaurant=original_restaurant,
                                                                 online=False).all()
        #context['profile_form'] = edit_profile_form
        return render(request, 'tartan_eats/restaurant-profile.html', context)


@login_required
def restaurant_order_list(request, status=None):
    if request.method == 'GET':
        context = {
            'restaurant': request.user.restaurant,
            'order_list': Order.objects
                .filter(restaurant=request.user.restaurant)
                .filter(order_status=status).all()
        }
        if status == None or status == 'pending':
            context['completed_class'] = ""
            context['in_delivery_class'] = ""
            context['pending_class'] = "active"
            context['order_list'] = Order.objects.filter(restaurant=request.user.restaurant).filter(
                order_status='pending').all()
        elif status == 'in-delivery':
            context['completed_class'] = ""
            context['in_delivery_class'] = "active"
            context['pending_class'] = ""
        else:
            context['completed_class'] = "active"
            context['in_delivery_class'] = ""
            context['pending_class'] = ""
        return render(request, 'tartan_eats/restaurant-order-list.html', context)


@login_required
def get_photo(request, user_id, pic_type):
    if pic_type == "restaurant":
        restaurant = get_object_or_404(Restaurant, user_id=user_id)
        # print('Picture #{} fetched from db: {} (type={})'.format(user——id, item.picture, type(item.picture)))
        # Maybe we don't need this check as form validation requires a picture be uploaded.
        # But someone could have delete the picture leaving the DB with a bad references.
        if not restaurant.restaurant_picture:
            raise Http404
        return HttpResponse(restaurant.restaurant_picture, restaurant.content_type)
    if pic_type == "cuisine":
        cuisine = get_object_or_404(Cuisine, id=user_id)
        # print('Picture #{} fetched from db: {} (type={})'.format(user——id, item.picture, type(item.picture)))
        # Maybe we don't need this check as form validation requires a picture be uploaded.
        # But someone could have delete the picture leaving the DB with a bad references.
        if not cuisine.cuisine_picture:
            raise Http404
        return HttpResponse(cuisine.cuisine_picture, cuisine.content_type)

@login_required
def restaurant_order(request, order_id):
    order = Order.objects.get(id=order_id)
    context = {
        'restaurant': request.user.restaurant,
        'order': order,
        'key': google_map_key
    }
    customer_address = order.real_address1 + " " + order.real_address2
    context['customer_full_address'] = customer_address
    status = order.order_status
    try:
        destination_id, destination_address = get_place_id(customer_address)
        context['destination_id'] = destination_id
        if order.order_status == 'pending':
            return render(request, 'tartan_eats/restaurant-pending-order.html', context)
        elif order.order_status == 'in-delivery':
            delivery = order.delivery
            context['realtime_position_id'] = delivery.realtime_position
            context['driver'] = order.delivery.driver
            return render(request, 'tartan_eats/restaurant-indelivery-order.html', context)
        elif order.order_status == 'completed':
            context['driver'] = order.delivery.driver
            return render(request, 'tartan_eats/restaurant-completed-order.html', context)
    except Exception:
        context = { 'restaurant': request.user.restaurant,
                    'key': google_map_key, 'order_list': Order.objects
            .filter(restaurant=request.user.restaurant)
            .filter(order_status=status).all(),
                    'error': "Invalid place Id. Cannot show order detail."}
        if status == 'pending':
            context['completed_class'] = ""
            context['in_delivery_class'] = ""
            context['pending_class'] = "active"
        elif status == 'in-delivery':
            context['completed_class'] = ""
            context['in_delivery_class'] = "active"
            context['pending_class'] = ""
        else:
            context['completed_class'] = "active"
            context['in_delivery_class'] = ""
            context['pending_class'] = ""
        return render(request, 'tartan_eats/restaurant-order-list.html', context)

def get_place_id(place_name):
    try:
        address = place_name
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={address}&inputtype=textquery" \
              f"&fields=formatted_address%2Cplace_id%2Cgeometry&key={google_map_key}"
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        place_id = response.json()['candidates'][0]['place_id']
        formatted_address = response.json()['candidates'][0]['formatted_address']
        return place_id, formatted_address
    except:
        raise Exception("Cannot find place id of this place: " + place_name)

def get_realtime_position_list(origin_id, destination_id):
    # waypoints = []
    # names = []
    search_nearby_distance = 500
    id1, name1 = get_nearby_place_id_name(origin_id, search_nearby_distance)
    id2, name2 = get_nearby_place_id_name(destination_id, search_nearby_distance)
    realtime_position_list = [id1, id2, name1, name2]
    print(realtime_position_list)
    return realtime_position_list


def get_nearby_place_id_name(start_place_id, search_nearby_distance):
    try:
        start_latitude, start_longitude = get_place_location(start_place_id)
        # search_nearby_distance unit:  meters
        search_nearby_keywords = 'restaurant'
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={start_latitude},{start_longitude}&radius" \
              f"={search_nearby_distance}&keyword={search_nearby_keywords}&key={google_map_key}"
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        place_id = response.json()['results'][0]['place_id']
        place_name = response.json()['results'][0]['name']
        print("nearby place name: " + place_name + " id: " + place_id)
        return place_id, place_name
    except:
        raise Exception("Cannot find valid place id for this place")

def get_place_location(place_id):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={google_map_key}"
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    location = response.json()['results'][0]['geometry']['location']
    return location['lat'], location['lng']

@login_required
def driver_pool(request, order_id):
    order = Order.objects.get(id=order_id)
    context = {
        'drivers': Driver.objects.all(),
        'order': order
    }
    return render(request, 'tartan_eats/driver-pool.html', context)

@login_required
def assign_driver(request, id, order_id):
    try:
        driver = get_object_or_404(Driver, user=id)
        order = Order.objects.get(id=order_id)
        customer_address = order.real_address1 + " " + order.real_address2
        origin_id, origin_address = get_place_id(order.restaurant.restaurant_address)
        print("origin")
        print(origin_id)
        print(origin_address)
        destination_id, destination_address = get_place_id(customer_address)
        print("destination")
        print(destination_id)
        print(destination_address)
        id1, name1 = get_nearby_place_id_name(origin_id, 500)
        print("place 1")
        print(id1)
        print(name1)
        id2, name2 = get_nearby_place_id_name(destination_id, 500)
        print("place 2")
        print(id2)
        print(name2)
        route_information_list = [origin_id, id1, id2, destination_id, origin_address, name1, name2,
                                  destination_address]
        route_information = '|'.join(route_information_list)
        # route_information format: origin_id|id1|id2|destination_id|origin|name1|name2|destination
        print(route_information)
        delivery = Delivery(order=order, driver=driver,
                            delivery_status='in-delivery',
                            # used for update
                            realtime_position=origin_id,
                            cnt=0,
                            route_information=route_information.replace(" ", ""))
        delivery.save()
        order.order_status = 'in-delivery'
        order.save()
        driver.avalable_status = "unavailable"
        driver.save()
        context = {'restaurant': request.user.restaurant,
                   'order_list': Order.objects.filter(restaurant=request.user.restaurant).filter(
                       order_status='in-delivery').all(), 'completed_class': "", 'in_delivery_class': "active",
                   'pending_class': ""}
        return render(request, 'tartan_eats/restaurant-order-list.html', context)
    except:
        # assign driver will not be successful, return back to driver pool
        context = {'restaurant': request.user.restaurant,
                   'order_list': Order.objects.filter(restaurant=request.user.restaurant).filter(
                       order_status='in-delivery').all(), 'completed_class': "", 'in_delivery_class': "active",
                   'pending_class': "",
                   'error': "Invalid place id; Cannot assign driver to this order; Please ignore this order"}
        return render(request, 'tartan_eats/driver-pool.html', context)

@login_required
def logout_action(request):
    logout(request)
    return redirect(reverse('login'))

# -------------- customer side---------tun----------------------#

@login_required
def customer_account(request):
    if request.method == 'GET':
        customer = User.objects.select_for_update().get(id=request.user.id).customer
        form = CustomerEditForm(instance=customer)
        context = {'customer': request.user.customer,
                   'form': form}
        return render(request, 'tartan_eats/customer-account.html', context)

    customer = User.objects.select_for_update().get(id=request.user.id).customer
    form = CustomerEditForm(request.POST, request.FILES, instance=customer)

    if not form.is_valid():
        context = {'customer': request.user.customer, 'form': form}
        return render(request, 'tartan_eats/customer-account.html', context)

    # pic = form.cleaned_data['customer_picture']
    # request.user.customer.customer_picture = pic
    # request.user.customer.content_type = pic.content_type
    customer.save()
    form = CustomerEditForm(instance=customer)
    context = {'message': 'profile updated!', 'customer': customer, 'form': form}
    return render(request, 'tartan_eats/customer-account.html', context)

@login_required
def customer_checkout(request, id):
    if request.method == 'GET':
        order = Order.objects.get(id=id)
        restaurant_id = order.restaurant.user.id
        if (order.subtotal == 0):
            redirect_url = "tartan_eats/customer-single-restaurant/"+restaurant_id+"/.html"
            return render(request, redirect_url, context)
        form = OrderForm(instance=order)
        order.tax = round(order.subtotal*0.07,2)
        order.total_amount = order.subtotal+order.restaurant.delivery_fee+ order.tax
        order.save()
        context = {'order_cuisines': order.order_cuisine.all(), 'form': form}
        return render(request, 'tartan_eats/customer-checkout.html', context)
    # else post
    order = Order.objects.select_for_update().get(id=id)
    form = OrderForm(request.POST, instance=order)

    if not form.is_valid():
        context = {'order_cuisines': order.order_cuisine.all(), 'form': form}
        return render(request, 'tartan_eats/customer-checkout.html', context)
    order.save()
    form = OrderForm(instance=order)
    context = {'order_cuisines': order.order_cuisine.all(), 'form': form}
    return render(request, 'tartan_eats/customer-checkout.html', context)

@login_required
def customer_history_order(request):
    context = {'orders': Order.objects.filter(customer=request.user.customer)}
    return render(request, 'tartan_eats/customer-history-order.html', context)

@login_required
def confirmation(request, id):
    context = {}
    order = Order.objects.get(id=id)
    order.order_status = 'pending'
    order.save()
    return render(request, 'tartan_eats/confirmation.html', context)

@login_required
# payment cancel
def oncancel(request, id):
    context = {'order': Order.objects.get(id=id)}
    order = Order.objects.get(id=id)
    order.order_status = 'adding'  # or not change
    order.save()
    return render(request, 'tartan_eats/oncancel.html', context)

def customer_cancel_order(request, id):
    context = {'order': Order.objects.get(id=id)}
    order = Order.objects.get(id=id)
    order.order_status = 'cancel'  # or not change
    order.save()
    return render(request, 'tartan_eats/cancel-order.html', context)

@login_required
def customer_order_detail(request, id):
    order = Order.objects.get(id=id)
    origin_id, origin_address = get_place_id(order.restaurant.restaurant_address)
    customer_address = order.real_address1 + " " + order.real_address2
    destination_id, destination_address = get_place_id(customer_address)
    context = {'order': order, 'order_cuisines': order.order_cuisine.all(), 'destination_id': destination_id,
               'customer_full_address': customer_address, 'key': google_map_key}
    try:
        if order.order_status == 'in-delivery' or 'completed':
            context['realtime_position_id'] = order.delivery.realtime_position
        else:
            context['realtime_position_id'] = origin_id
        return render(request, 'tartan_eats/customer-order-detail.html', context)
    except Delivery.DoesNotExist:
        context['realtime_position_id'] = origin_id
        return render(request, 'tartan_eats/customer-order-detail.html', context)
    except Exception:
        context = {'orders': Order.objects.filter(customer=request.user.customer),
                   'error': "Invalid place id, please check your address and order again"}
        return render(request, 'tartan_eats/customer-history-order.html', context)


def get_customer_photo(request):
    # customer = User.objects.select_for_update().get(id=request.user.id).customer
    print("executed")
    print(request.user.customer.customer_picture)
    user = get_object_or_404(User, id=request.user.id)
    print('Picture #{} fetched from db: {} (type={})'.format(request.user.id, user.customer.customer_picture,
                                                             type(user.customer.customer_picture)))
    if not user.customer.customer_picture:
        raise Http404
    return HttpResponse(user.customer.customer_picture, user.customer.content_type)