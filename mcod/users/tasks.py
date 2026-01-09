from django.apps import apps

from mcod.core.tasks import extended_shared_task


@extended_shared_task
def send_registration_email_task(user_id):
    model = apps.get_model("users.User")
    user = model.objects.filter(pk=user_id, state="pending").first()
    num_sent = user.send_registration_email() if user else 0
    return {"num_sent": num_sent}
