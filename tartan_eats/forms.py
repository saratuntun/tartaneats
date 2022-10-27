import email
from tokenize import blank_re

from django import forms
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from tartan_eats.models import Customer, Restaurant, Driver, Cuisine, Order
from phonenumber_field.formfields import PhoneNumberField

MAX_UPLOAD_SIZE = 2500000

class CuisineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cuisine_name'].required = True
        self.fields['cuisine_description'].required = True
        self.fields['price'].required = True

    class Meta:
        model = Cuisine
        fields = ('cuisine_name', 'cuisine_description', 'cuisine_picture', 'price')
        widgets = {
            'cuisine_picture': forms.FileInput(attrs={
                'id': 'id_cuisine_picture',
            }),
        }

    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()
        if cleaned_data['price'] <= 0:
            raise forms.ValidationError("The number of price should be positive. Please try again.")
        return cleaned_data


class CustomerRegisterForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            'firstname', 'lastname', 'email', 'phone', 'address1', 'address2', 'zipcode', 'city', 'customer_picture')


class RestaurantRegisterForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['restaurant_name', 'email', 'phone', 'restaurant_address',
                  'restaurant_description', 'delivery_fee'
            , 'restaurant_picture']
        widgets = {
            'email': forms.EmailInput(),
            'restaurant_picture': forms.FileInput(attrs={
                'id': 'id_profile_picture',
            }),
        }

    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()
        return cleaned_data


class RestaurantEditForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['restaurant_name', 'email', 'phone', 'restaurant_address',
                  'restaurant_description', 'delivery_fee', 'restaurant_picture']
        widgets = {
            'email': forms.EmailInput(),
            'restaurant_picture': forms.FileInput(attrs={
                'id': 'id_profile_picture',
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('real_first_name', 'real_last_name', 'real_email', 'real_phone', 'real_address1', 'real_address2')
        widgets = {
            'real_first_name': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'real_last_name': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'real_email': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'real_phone': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'real_address1': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'real_address2': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
        }
        labels = {
            'real_first_name': "First Name:   ",
            'real_last_name': "Last Name:  ",
            'real_email': "Email:  ",
            'real_phone': "Phone Number:  ",
            'real_address1': "Address1:  ",
            'real_address2': "Address2:  "
        }
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super().clean()
        return cleaned_data

class DriverRegisterForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ('firstname', 'lastname', 'email', 'phone', 'driver_picture')
        widgets = {
            'firstname': forms.TextInput(attrs={'placeholder': "First Name",
                                                'class': "form-control"}),
            'lastname': forms.TextInput(attrs={'placeholder': "Last Name",
                                               'class': "form-control"}),
            'email': forms.EmailInput(attrs={'placeholder': "Email",
                                             'class': "form-control"}),
            'phone': forms.TextInput(attrs={'placeholder': "Phone",
                                            'class': "form-control"}),
            'driver_picture': forms.FileInput(attrs={
                'class': "form-control", 'id': 'id_profile_picture', })
        }
        labels = {
            'driver_picture': "Upload Picture:"
        }


class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            'firstname', 'lastname', 'email', 'phone', 'address1', 'address2', 'zipcode', 'city', 'customer_picture')
        widgets = {
            'customer_picture': forms.FileInput(attrs={'id': 'id_customer_profile_picture'}),
            'email': forms.EmailInput(),
            'firstname': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'lastname': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'email': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'phone': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'address1': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'address2': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'zipcode': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80}),
            'city': forms.Textarea(attrs={'type': "text", 'maxlength': 20, 'rows': 1, 'cols': 80})
        }
        labels = {
            'customer_picture': "Upload Profile Picture:"
        }

    def clean_picture(self):
        customer_picture = self.cleaned_data['customer_picture']
        if not customer_picture or not hasattr(customer_picture, 'content_type'):
            raise forms.ValidationError('You must upload a picture')
        if not customer_picture.content_type or not customer_picture.content_type.startswith('image'):
            raise forms.ValidationError('File type is not image')
        if customer_picture.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return customer_picture
