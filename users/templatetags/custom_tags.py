from django import template
from users.models import Approver

register = template.Library()

@register.filter
def is_approver(user):
    return Approver.objects.filter(user=user).exists()
