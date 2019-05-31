# from django.db import models
# from django.contrib.auth import get_user_model
#
# from mcod.lib.model_mixins import IndexableMixin

# User = get_user_model()


class UsersFollowingMixin:
    @property
    def users_following_list(self):
        return [user.id for user in self.users_following.all()]


# class FollowingModel(models.Model, IndexableMixin):
#     follower = models.ForeignKey(User, on_delete=models.CASCADE)
#
#     @property
#     def object_id(self):
#         return getattr(self, self.object_type).id
#
#     @property
#     def object_type(self):
#         return self._meta.db_table[len('user_following_'):]
#
#     class Meta:
#         abstract = True
#
# class UserFollowingApplication(FollowingModel):
#     application = models.ForeignKey('applications.Application', on_delete=models.CASCADE)
#
#     class Meta:
#         db_table = 'user_following_application'
#
#
# class UserFollowingArticle(FollowingModel):
#     article = models.ForeignKey('articles.Article', on_delete=models.CASCADE)
#
#     class Meta:
#         db_table = 'user_following_article'
#
#
# class UserFollowingDataset(FollowingModel):
#     dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE)
#
#     class Meta:
#         db_table = 'user_following_dataset'
