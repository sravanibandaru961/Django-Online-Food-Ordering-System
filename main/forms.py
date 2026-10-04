"""
from django import forms
from .models import Item

class AddForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('created_by',
        'title', 'image', 'description', 'price', 'pieces', 'instructions', 'labels', 'label_colour', 'slug')
        """

from django import forms
from .models import DishRequest



class DishRequestForm(forms.ModelForm):

    class Meta:
        model = DishRequest
        fields = ['dish_name', 'description']

        widgets = {
            'dish_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter the dish you want'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Tell us what you are looking for',
                    'rows': 4
                }
            ),
        }