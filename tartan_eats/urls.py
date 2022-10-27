"""tartan_eats URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from tartan_eats import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_action,name='home'),
    path('accounts/', include('allauth.urls')),
    path('login', views.login_action, name='login'),
    path('register', views.register_action, name='register'),
    path('register-customer', views.register_customer, name='register-customer'),
    path('register-restaurant', views.register_restaurant, name='register-restaurant'),
    path('register-driver', views.register_driver, name='register-driver'),
    path('logout', LogoutView.as_view(), name='logout'),

    # ke
    # path('restaurant-pending-order', views.restaurant_pending_order, name="restaurant-pending-order"),
    path('driver-pool/<int:order_id>', views.driver_pool, name="driver-pool"),
    path('assign-driver/<int:id>, <int:order_id>', views.assign_driver, name='assign-driver'),
    path('driver-home', views.driver_home, name="driver-home"),
    path('driver-photo', views.get_driver_picture, name='driver-photo'),
    path('driver-order-indelivery', views.driver_order_indelivery, name="driver-order-indelivery"),
    path('driver-order-completed', views.driver_order_completed, name="driver-order-completed"),
    path('driver-change-delivery', views.driver_change_delivery, name="driver-change-delivery"),
    path('driver-change-status', views.driver_change_status, name="driver-change-status"),
    # end ke

    #chu
    path('customer-home', views.customer_home, name="customer-home"),
    #single restaurant
    path('customer-single-restaurant/<int:restaurant_id>', views.single_restaurant, name='customer-single-restaurant'),
    #shopping cart 
    path('add-to-cart/<int:cuisine_id>', views.add_to_cart, name='add-to-cart'),
    path('delete-from-cart/<int:cuisine_id>', views.delete_from_cart, name='delete-from-cart'),
    path('get-cart-list/<int:restaurant_id>', views.get_cart_list_json_dumps),

    # yanjun
    path('restaurant-home/<int:cuisine_id>', views.restaurant_home, name="restaurant-home"),
    path('restaurant-home', views.restaurant_home, name="restaurant-home"),
    path('order-list', views.restaurant_order_list, name='order-list'),
    path('order-list/<str:status>', views.restaurant_order_list, name='order-list'),
    path('res-photo/<int:user_id>, <str:pic_type>', views.get_photo, name='res-photo'),
    path('restaurant-order/<int:order_id>', views.restaurant_order, name='restaurant-order'),
    path('driver-update-location', views.driver_update_location, name='driver-update-location'),

    #tuntun
    path('customer-account', views.customer_account, name='customer-account'),
    path('customer-checkout/<int:id>', views.customer_checkout, name='customer-checkout'),
    path('confirmation/<int:id>', views.confirmation, name='confirmation'),
    path('oncancel/<int:id>', views.oncancel, name='oncancel'),
    path('cancel-order/<int:id>', views.customer_cancel_order, name='cancel-order'),
    path('customer-history-order', views.customer_history_order, name='customer-history-order'),
    path('customer-order-detail/<int:id>', views.customer_order_detail, name='customer-order-detail'),
    path('customer-photo', views.get_customer_photo, name='customer-photo'),
    path('accounts/', include('allauth.urls')),
    path('logout', LogoutView.as_view(), name='logout'),
    path('order-list', views.restaurant_order_list, name='order-list')
]

