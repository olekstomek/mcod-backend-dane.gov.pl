from django_tqdm import BaseCommand
from elasticsearch_dsl import Search

from mcod.histories.documents import HistoriesDoc


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = Search(index="histories").filter('term', table_name='user')
        self.progres_bar = self.tqdm(desc="Deleting", total=self.query.count())

    def delete_documents(self):
        for hit in self.query.scan():
            self.progres_bar.update(1)
            doc = HistoriesDoc.get(hit.id)
            doc.delete()

    def handle(self, *args, **kwargs):
        self.delete_documents()
        print("Done")
