from statistics import mode

from django.contrib.auth.models import User
from django.db import models
from pyexpat import model
# a phone number package. install by: pip install django-phonenumber-field
# also pip install phonenumbers
# it is a char field. MyModel(phone_number='+41524204242')
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator, MinValueValidator


class Role(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    type = models.CharField(max_length=200)

    def __str__(self):
        return 'user=' + str(self.user) + ',type="' + str(self.type) + '"'


class Customer(models.Model):
    # user = models.ForeignKey(allauth.app_settings.USER_MODEL, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    customer_picture = models.FileField(blank=True)
    firstname = models.CharField(max_length=200)
    lastname = models.CharField(max_length=200)
    email =  models.CharField(max_length=200)
    phone =  PhoneNumberField(null=False, blank=False)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50, default="image/jpeg")


class Restaurant(models.Model):
    # user and restaurant cannot be one on one, because user are not all restaurant.
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    restaurant_name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone = PhoneNumberField(null=False, blank=False)
    restaurant_address = models.CharField(max_length=500)
    restaurant_description = models.CharField(max_length=2000)
    delivery_fee = models.FloatField(null=True, blank=True, default=None)
    # venmo_account = models.CharField(max_length=500)
    restaurant_picture = models.FileField(blank=True)
    # restaurant_picture = models.ImageField(blank=True, upload_to='static/tartan_eats/images/')
    # # for restaurant picture
    content_type = models.CharField(max_length=200, default="image/jpeg")


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    firstname = models.CharField(max_length=200)
    lastname = models.CharField(max_length=200)
    email =  models.CharField(max_length=200)
    phone =  PhoneNumberField(null=False, blank=False)
    avalable_status = models.CharField(max_length=200) # available, unavailable
    driver_picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=200, default="image/jpeg")


class Order(models.Model):
    customer = models.ForeignKey(Customer, default=None, on_delete=models.PROTECT)
    restaurant = models.ForeignKey(Restaurant, default=None, on_delete=models.PROTECT)
    real_first_name = models.CharField(max_length=100)
    real_last_name = models.CharField(max_length=100)
    real_email =  models.CharField(max_length=200)
    real_phone =  PhoneNumberField(null=False, blank=False)
    real_address1 = models.CharField(max_length=200)
    real_address2 = models.CharField(max_length=200)
    subtotal = models.FloatField(null=True, blank=True, default=None)
    tax = models.FloatField(null=True, blank=True, default=None)
    total_amount = models.FloatField(null=True, blank=True, default=None)
    order_time = models.DateTimeField()
    order_status = models.CharField(max_length=100)

class Cuisine(models.Model):
    restaurant = models.ForeignKey(Restaurant, default=None, on_delete=models.PROTECT)
    cuisine_name = models.CharField(max_length=200)
    cuisine_description = models.CharField(max_length=2000)
    price = models.FloatField(null=True, blank=True, default=None)
    cuisine_picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=200, default="image/jpeg")
    online = models.BooleanField(default=True)

    def __str__(self):
        return 'id=' + str(self.id) + ',restaurant="' + self.restaurant.restaurant_name + '" cuisine_name = ' + str(
            self.cuisine_name) + " cuisine_description= " + str(self.cuisine_description) \
               + " price= " + str(self.price) + " content type = " + str(self.content_type)


# order = Order(customer = User.objects.get(id=1).customer, restaurant=User.objects.get(id=2).restaurant, subtotal = 1, tax = 1, total_amount= 2, order_time='2022-03-21 10:12', order_status='pending')

# order.save()
class Order_Cuisine(models.Model):
    order = models.ForeignKey(Order, default=None, on_delete=models.PROTECT, related_name='order_cuisine')
    cuisine = models.ForeignKey(Cuisine, default=None, on_delete=models.PROTECT, related_name='order_cuisine')
    item_quantity = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return 'order=' + str(self.order) + ',cuisine="' + self.cuisine.cuisine_name + ',item_quantity="' + str(
            self.item_quantity)


class Delivery(models.Model):
    order = models.OneToOneField(Order, default=None, on_delete=models.PROTECT)
    driver = models.ForeignKey(Driver, default=None, on_delete=models.PROTECT)
    delivery_status = models.CharField(max_length=100)
    # used for google map and route update
    realtime_position = models.CharField(max_length=2000, default="")
    cnt = models.IntegerField(default=0)
    route_information = models.CharField(max_length=2000, default="")
