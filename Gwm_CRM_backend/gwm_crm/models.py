from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Company(models.Model):
    name = models.CharField(max_length=50, unique=True)
    website = models.URLField(max_length=200, unique=True, blank=True)
    country = models.CharField(max_length=5, choices=(('a', 'A'), ('b', 'B'), ('c', 'C')))
    industry_category = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(16)])
    activity_level = models.CharField(max_length=10, choices=(('active', 'Active'), ('passive', 'Passive')))
    acquired_via = models.CharField(max_length=100)
    lead_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    notes = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.country})"
    

class Opportunity(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='opportunities')
    stage = models.CharField(max_length=20, choices =(('lead', 'Lead'), ('qualified', 'Qualified'), ('negotiation', 'Negotiation'), ('won', 'Won'), ('lost', 'Lost')))
    expected_value = models.IntegerField()
    expected_close_date = models.DateTimeField(null=True, blank=True)
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        default=0,
    )

    def __str__(self):
        return f"{self.company}: {self.stage} (${self.expected_value})" 

class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts')
    full_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company_email = models.EmailField()
    personal_email = models.EmailField()
    phone_office = models.CharField(max_length=20)
    phone_mobile = models.CharField(max_length=20)
    address = models.TextField()
    customer_specific_conditions = models.CharField(max_length=200)
    business_card = models.FileField(
        upload_to='business_cards/',
        blank=True,             
        verbose_name="Business Card"
    )
    # document = models.FileField(
    #     upload_to='contact_documents/',
    #     blank=True,
    #     verbose_name="Document"
    #     )

    def __str__(self):
        return f"{self.full_name} - {self.position} @ {self.company}"
    
class ContactDocument(models.Model):
    contact = models.ForeignKey(
        Contact, 
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.FileField(
        upload_to='contact_documents/%Y/%m/%d/'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name or 'Document'} for {self.contact}"
    
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    category = models.CharField(max_length=200)
    price_list = models.FileField(
        upload_to='price_lists/',
        blank=True,             
        verbose_name="Price List"
        )
    price_list_expiry = models.DateTimeField(null=True, blank=True)
    volume_offered = models.CharField(max_length=200)
    delivery_terms = models.CharField(max_length=200)
    packaging = models.CharField(max_length=200)
    payment_terms = models.CharField(max_length=200)
    # currency = (dropdownlist)
    product_specifications = models.TextField()
    target_price = models.IntegerField()
    
    def __str__(self):
        return f"{self.company}: {self.category} (Target: ${self.target_price})"
    
class Interaction(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interactions'
    )
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=200)
    status = models.CharField(choices=(('green', 'Green'), ('yellow', 'Yellow'), ('red', 'Red')), default='green')
    summary = models.TextField()
    # attachments = 
    # assigned_to = 

    def __str__(self):
        contact_str = f" with {self.contact}" if self.contact else ""
        return f"{self.company}{contact_str} - {self.type} ({self.date.date()})" 
