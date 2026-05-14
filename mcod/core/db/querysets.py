import base64
import pickle
import zlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, Type

from django.apps import apps
from django.db.models import QuerySet


@dataclass(frozen=True)
class QuerySetDTO:
    app: str
    model_name: str
    pickled_query: str

    @property
    def model_label(self) -> str:
        return f"{self.app}.{self.model_name}"

    @classmethod
    def from_queryset(cls, queryset: QuerySet) -> "QuerySetDTO":
        """
        Serializes the QuerySet's query object into a compressed string.
        """
        model_label: str = queryset.model._meta.label
        _app, _model_name = model_label.split(".")

        # We pickle only .query because it's a lightweight SQL 'recipe'.
        # The full QuerySet is unpicklable as it contains active DB connections and result caches.
        serialized_query: bytes = pickle.dumps(queryset.query)

        # Compress the pickle to reduce memory footprint and transport time
        compressed_query: bytes = zlib.compress(serialized_query)

        # Encode to base64 for 'safe transport' through JSON-based Celery brokers.
        # This converts raw binary bytes into an ASCII string that won't break JSON parsers.
        payload: str = base64.b64encode(compressed_query).decode("ascii")

        return cls(
            app=_app,
            model_name=_model_name,
            pickled_query=payload,
        )

    def to_queryset(self) -> QuerySet:
        """
        Reconstructs the QuerySet from the serialized query payload.
        """
        # Get the model class from the Django app registry
        model_class: Type[Any] = apps.get_model(self.app, self.model_name)

        # Decode and decompress the payload
        compressed_query: bytes = base64.b64decode(self.pickled_query.encode("ascii"))
        serialized_query: bytes = zlib.decompress(compressed_query)

        # Restore the query object
        query_obj: Any = pickle.loads(serialized_query)

        # Create a new QuerySet and attach the restored query object
        # Note: This is a standard way to restore filtered QuerySets in Django
        new_queryset: QuerySet = model_class.objects.all()
        new_queryset.query = query_obj

        return new_queryset

    def asdict(self) -> Dict[str, str]:
        """
        Returns a dictionary representation for easy serialization (e.g., for Celery).
        """
        return asdict(self)
