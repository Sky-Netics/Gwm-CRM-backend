from django.contrib import admin
from .models import Company, Opportunity, Product, Contact, Interaction

admin.site.register(Company)
admin.site.register(Contact)
admin.site.register(Opportunity)
admin.site.register(Product)
admin.site.register(Interaction)