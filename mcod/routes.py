# -*- coding: utf-8 -*-
from mcod.applications import views as app_views
from mcod.articles import views as article_views
from mcod.core.api.utils import views as core_views
from mcod.datasets import views as dataset_views
from mcod.following.api import views as following_views
from mcod.histories.api import views as history_views
from mcod.organizations import views as org_views
from mcod.resources import views as res_views
from mcod.searchhistories import views as searchhistory_views
from mcod.tools import views as tools_views
from mcod.users import views as user_views
from mcod.watchers.api import views as watcher_views
from mcod.suggestions import views as submission_views

routes = [
    # Tools & utilities
    ('/stats', tools_views.StatsView()),
    ('/cluster/health', core_views.ClusterHealthView()),
    ('/cluster/explain', core_views.ClusterAllocationView()),
    ('/cluster/state', core_views.ClusterStateView()),
    ('/spec', core_views.OpenApiSpec()),
    ('/spec/{version}', core_views.OpenApiSpec()),
    ('/doc/', core_views.SwaggerView()),
    # User
    ('/auth/login', user_views.LoginView()),
    ('/auth/logout', user_views.LogoutView()),
    ('/auth/password/reset', user_views.ResetPasswordView()),
    ('/auth/password/reset/{token:uuid}/', user_views.ConfirmResetPasswordView()),
    ('/auth/password/change', user_views.ChangePasswordView()),
    ('/auth/user', user_views.AccountView()),
    ('/auth/registration', user_views.RegistrationView()),
    ('/auth/registration/verify-email/{token:uuid}/', user_views.VerifyEmailView()),
    ('/auth/registration/resend-email', user_views.ResendActivationEmailView()),
    ('/auth/subscriptions', watcher_views.SubscriptionsView()),
    ('/auth/subscriptions/{id:int}', watcher_views.SubscriptionView()),
    ('/auth/subscriptions/{id:int}/notifications', watcher_views.NotificationsView()),
    ('/auth/notifications', watcher_views.NotificationsView()),
    ('/auth/notifications/{id:int}', watcher_views.NotificationView()),
    # Applications
    ('/applications', app_views.ApplicationSearchApiView()),
    ('/applications/{id:int}', app_views.ApplicationApiView()),
    ('/applications/{id:int},{slug}', app_views.ApplicationApiView()),
    ('/applications/{id:int}/datasets', app_views.ApplicationDatasetsView()),
    ('/applications/{id:int},{slug}/datasets', app_views.ApplicationDatasetsView()),
    ('/applications/{id:int}/follow', following_views.FollowApplication()),
    ('/applications/{id:int},{slug}/follow', following_views.FollowApplication()),
    ('/applications/followed', following_views.ListOfFollowedApplications()),
    ('/applications/suggest', app_views.ApplicationSubmitView()),
    ('/applications/submissions', app_views.ApplicationSubmitView()),
    # Articles
    ('/articles', article_views.ArticlesView()),
    ('/articles/{id:int}', article_views.ArticleView()),
    ('/articles/{id:int},{slug}', article_views.ArticleView()),
    ('/articles/{id:int}/datasets', article_views.ArticleDatasetsView()),
    ('/articles/{id:int},{slug}/datasets', article_views.ArticleDatasetsView()),
    ('/articles/{id:int}/follow', following_views.FollowArticle()),
    ('/articles/{id:int},{slug}/follow', following_views.FollowArticle()),
    ('/articles/followed', following_views.ListOfFollowedArticles()),
    # Organizations
    ('/institutions', org_views.InstitutionSearchView()),
    ('/institutions/{id:int}', org_views.InstitutionApiView()),
    ('/institutions/{id:int},{slug}', org_views.InstitutionApiView()),
    ('/institutions/{id:int}/datasets', org_views.InstitutionDatasetSearchApiView()),
    ('/institutions/{id:int},{slug}/datasets', org_views.InstitutionDatasetSearchApiView()),

    # Datasets
    ('/datasets', dataset_views.DatasetSearchView()),
    ('/datasets/{id:int}', dataset_views.DatasetApiView()),
    ('/datasets/{id:int},{slug}', dataset_views.DatasetApiView()),
    ('/datasets/{id:int}/resources', dataset_views.DatasetResourceSearchApiView()),
    ('/datasets/{id:int},{slug}/resources', dataset_views.DatasetResourceSearchApiView()),
    # ('/datasets/{id:int}/resources/{resource_id:int}', dataset_views.DatasetResourceView()),
    ('/datasets/{id:int}/follow', following_views.FollowDataset()),
    ('/datasets/{id:int},{slug}/follow', following_views.FollowDataset()),
    ('/datasets/followed', following_views.ListOfFollowedDatasets()),
    ('/datasets/{id:int}/comments', dataset_views.DatasetCommentSearchApiView()),
    ('/datasets/{id:int},{slug}/comments', dataset_views.DatasetCommentSearchApiView()),
    # Resources
    ('/resources/', res_views.ResourcesView()),
    ('/resources/{id:int}', res_views.ResourceView()),
    ('/resources/{id:int},{slug}', res_views.ResourceView()),
    ('/resources/{id:int}/data', res_views.ResourceTableView()),
    ('/resources/{id:int},{slug}/data', res_views.ResourceTableView()),
    # ('/resources/{id:int}/table', res_views.ResourceTableView()),
    ('/resources/{id:int}/data/{row_id:uuid}', res_views.ResourceTableRowView()),
    ('/resources/{id:int},{slug}/data/{row_id:uuid}', res_views.ResourceTableRowView()),
    # ('/resources/{id:int}/data/{row_id:uuid}', res_views.ResourceTableRowView()),
    ('/resources/{id:int}/data/spec/', res_views.ResourceTableSpecView()),
    ('/resources/{id:int},{slug}/data/spec/', res_views.ResourceTableSpecView()),
    ('/resources/{id:int}/data/spec/{version}', res_views.ResourceTableSpecView()),
    ('/resources/{id:int},{slug}/data/spec/{version}', res_views.ResourceTableSpecView()),
    ('/resources/{id:int}/data/doc/', res_views.ResourceSwaggerView()),
    ('/resources/{id:int},{slug}/data/doc/', res_views.ResourceSwaggerView()),
    # Depricated views
    ('/resources/{id:int}/incr_download_count', res_views.ResourceDownloadCounter()),
    ('/resources/{id:int},{slug}/incr_download_count', res_views.ResourceDownloadCounter()),
    ('/resources/{id:int}/comments', res_views.ResourceCommentsView()),
    ('/resources/{id:int},{slug}/comments', res_views.ResourceCommentsView()),
    ('/resources/{id:int}/file', res_views.ResourceFileDownloadView()),
    ('/resources/{id:int},{slug}/file', res_views.ResourceFileDownloadView()),
    # Histories
    ('/histories/', history_views.HistoriesView()),
    ('/histories/{id:int}', history_views.HistoryView()),
    ('/searchhistories/', searchhistory_views.SearchHistoriesView()),
    ('/submissions', submission_views.SubmissionView())

]

routes.extend(list(map(lambda x: ("/{api_ver}" + x[0], x[1]), routes)))
