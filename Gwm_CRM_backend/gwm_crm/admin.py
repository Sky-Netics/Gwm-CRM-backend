from django.contrib import admin
from .models import Company, Opportunity, Product, Contact, Interaction, Task, Meeting, Notification, Campaign

admin.site.register(Company)
admin.site.register(Contact)
admin.site.register(Opportunity)
admin.site.register(Product)
admin.site.register(Interaction)
admin.site.register(Task)
admin.site.register(Meeting)
admin.site.register(Notification)
admin.site.register(Campaign)
