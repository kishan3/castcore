# import datetime
# from haystack import indexes
# from .models import Job


# class JobIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True)
#     title = indexes.CharField(null=True, model_attr='title')
#     role_position = indexes.CharField(null=True, model_attr='role_position')
#     ages = indexes.MultiValueField(null=True, model_attr="ages")
#     location = indexes.CharField(model_attr='location__name_std')

#     def get_model(self):
#         return Job

#     def index_queryset(self, using=None):
#         """Used when the entire index for model is updated."""
#         return self.get_model().objects.filter(updated_at__lte=datetime.datetime.now())
