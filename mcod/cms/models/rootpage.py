from hypereditor.fields import HyperFieldPanel
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.api import APIField
from wagtail.api.v2.serializers import StreamField as StreamFieldSerializer
from wagtail.core.fields import StreamField

from mcod.cms.api.fields import HyperEditorJSONField, LocalizedHyperField
from mcod.cms.blocks.common import CarouselBlock
from mcod.cms.models.base import BasePage
from mcod.unleash import is_enabled


class RootPage(BasePage):
    over_login_section_cb = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                        verbose_name='Blok nad paskiem logowania',
                                        help_text='TODO: napisać'
                                        )
    over_search_field_cb = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                       verbose_name='Blok pod wyszukiwarką',
                                       help_text='TODO: napisać'
                                       )
    over_latest_news_cb = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                      verbose_name='Blok nad sekcją "Aktualności"',
                                      help_text='TODO: napisać'
                                      )
    over_login_section_cb_en = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                           verbose_name='Blok nad paskiem logowania',
                                           help_text='TODO: napisać'
                                           )
    over_search_field_cb_en = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                          verbose_name='Blok pod wyszukiwarką',
                                          help_text='TODO: napisać'
                                          )
    over_latest_news_cb_en = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                         verbose_name='Blok nad sekcją "Aktualności"',
                                         help_text='TODO: napisać'
                                         )

    footer_nav = LocalizedHyperField(default=None, blank=True, null=True, verbose_name='Stopka - sekcja nawigacji')
    footer_nav_en = LocalizedHyperField(default=None, blank=True, null=True, verbose_name='Stopka - sekcja nawigacji')

    footer_logos = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                               verbose_name='Stopka - sekcja logo')
    footer_logos_en = StreamField(CarouselBlock(max_num=5, required=False), default=None, blank=True,
                                  verbose_name='Stopka - sekcja logo')

    parent_page_types = ['wagtailcore.Page']

    fixed_url_path = ''

    header_and_nav_management = is_enabled('S42_cms_header_nav_manage.be')

    api_fields = BasePage.api_fields + [
        APIField('over_login_section_cb', serializer=StreamFieldSerializer(source='over_login_section_cb_i18n')),
        APIField('over_search_field_cb', serializer=StreamFieldSerializer(source='over_search_field_cb_i18n')),
        APIField('over_latest_news_cb', serializer=StreamFieldSerializer(source='over_latest_news_cb_i18n')),
    ]

    content_panels_pl = BasePage.content_panels_pl + [
        StreamFieldPanel('over_login_section_cb'),
        StreamFieldPanel('over_search_field_cb'),
        StreamFieldPanel('over_latest_news_cb'),
    ]

    content_panels_en = BasePage.content_panels_en + [
        StreamFieldPanel('over_login_section_cb_en'),
        StreamFieldPanel('over_search_field_cb_en'),
        StreamFieldPanel('over_latest_news_cb_en'),

    ]

    i18n_fields = BasePage.i18n_fields + ['over_login_section_cb', 'over_search_field_cb', 'over_latest_news_cb']
    if header_and_nav_management:
        i18n_fields += ['footer_nav', 'footer_logos']
        api_fields += [APIField('footer_nav', serializer=HyperEditorJSONField(source='footer_nav_i18n')),
                       APIField('footer_logos', serializer=StreamFieldSerializer(source='footer_logos_i18n'))]
        content_panels_pl += [HyperFieldPanel('footer_nav'),
                              StreamFieldPanel('footer_logos')]
        content_panels_en += [HyperFieldPanel('footer_nav_en'),
                              StreamFieldPanel('footer_logos_en')]

    class Meta:
        verbose_name = "Strona główna"
        verbose_name_plural = "Strony główne"

    def get_copyable_fields(self):
        page_fields = ['over_login_section_cb', 'over_search_field_cb', 'over_latest_news_cb']
        if self.header_and_nav_management:
            page_fields += ['footer_nav', 'footer_logos']
        return super().get_copyable_fields() + page_fields
