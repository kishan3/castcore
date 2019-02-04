from haystack import indexes
from .models import Education, Experience, SearchableField


class EducationIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    field_of_study_auto = indexes.EdgeNgramField(null=True, model_attr='field_of_study')
    degree_auto = indexes.EdgeNgramField(null=True, model_attr='degree')

    def get_model(self):
        return Education

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class ExperienceIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.EdgeNgramField(document=True, use_template=True)
    production_house_auto = indexes.EdgeNgramField(null=True, model_attr='production_house')
    role_auto = indexes.EdgeNgramField(null=True, model_attr='role')

    def get_model(self):
        return Experience

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class SearchableFieldIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    value_auto = indexes.EdgeNgramField(null=True, model_attr='value')
    field_name = indexes.CharField(null=True, model_attr='field_name')

    def get_model(self):
        return SearchableField

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
