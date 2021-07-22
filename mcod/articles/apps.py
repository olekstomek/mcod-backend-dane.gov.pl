from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class ArticlesConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.articles'
    verbose_name = _('Articles')

    def ready(self):
        from mcod.articles.models import Article, ArticleTrash, ArticleCategory
        self.connect_core_signals(Article)
        self.connect_core_signals(ArticleTrash)
        self.connect_core_signals(ArticleCategory)
        self.connect_m2m_signal(Article.datasets.through)
        self.connect_m2m_signal(Article.tags.through)
        # self.connect_common_index_signals(Article)
