# import pytest
# from django.template.loader import render_to_string
# from mcod.suggestions.models import Suggestion
# from constance import config
# from django.utils.translation import gettext_lazy as _
#
#
# @pytest.mark.django_db
# def test_create_suggestion(mailoutbox):
#     assert len(mailoutbox) == 0
#
#     suggestion = Suggestion()
#     suggestion.notes = "Lorem ipsum"
#     suggestion.save()
#
#     assert suggestion.created
#     assert suggestion.id
#
#     s = Suggestion.objects.get(pk=suggestion.id)
#
#     assert s.send_date
#     assert len(mailoutbox) == 1
#     m = mailoutbox[0]
#     assert m.subject == _('Resource demand reported')
#     assert m.body == render_to_string('mails/data-suggestion.txt', {"notes": suggestion.notes})
#     assert list(m.to) == [config.CONTACT_MAIL]
#     assert m.from_email == config.NO_REPLY_EMAIL
