from mcod.core.api.rdf.registry import registry
from mcod.core.tasks import extended_shared_task


@extended_shared_task
def update_graph_task(app_label, object_name, instance_id):
    registry.process_graph('update', app_label, object_name, instance_id)


@extended_shared_task
def create_graph_task(app_label, object_name, instance_id):
    registry.process_graph('create', app_label, object_name, instance_id)


@extended_shared_task
def create_graph_with_related_update_task(app_label, object_name, instance_id):
    registry.process_graph('create_with_related_update', app_label, object_name, instance_id)


@extended_shared_task
def update_graph_with_related_task(app_label, object_name, instance_id):
    registry.process_graph('update_with_related', app_label, object_name, instance_id)


@extended_shared_task
def update_graph_with_conditional_related_task(app_label, object_name, instance_id):
    registry.process_graph('update_with_conditional_related', app_label, object_name, instance_id)


@extended_shared_task
def update_related_graph_task(app_label, object_name, instance_id):
    registry.process_graph('update_related', app_label, object_name, instance_id)


@extended_shared_task
def delete_graph_task(app_label, object_name, instance_id):
    registry.process_graph('delete', app_label, object_name, instance_id)


@extended_shared_task
def delete_graph_with_related_update_task(app_label, object_name, instance_id, related_models):
    registry.process_graph('delete_with_related_update', app_label,
                           object_name, instance_id, related_models=related_models)


@extended_shared_task
def delete_sub_graphs(app_label, object_name, instance_id):
    registry.process_graph('delete_sub_graphs', app_label, object_name, instance_id)
