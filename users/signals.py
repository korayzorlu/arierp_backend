from users.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Profile
from companies.models import Company,UserCompany
from subscriptions.models import Subscription

@receiver(post_save, sender=User)
def create_related_models(sender, instance, created, **kwargs):
    if created:
        # Kullanıcı ilk defa oluşturuluyorsa ilişkili modelleri oluştur
        instance.is_email_verified = True
        instance.save()
        profile = Profile.objects.create(user=instance)
        profile.save()
        # Diğer bağlı modeller varsa onları da burada oluştur
        company = Company.objects.filter().first()
        user_company = UserCompany.objects.create(
            user = instance,
            company = company,
            is_active = True,
            is_admin = False
        )
        user_company.save()

        subscription = Subscription.objects.create(user = instance)
        subscription.save()