"""
Legacy direct export/import wrapper module.
"""

from scripts.dynamic_data_tool import export_rel, import_rel, export_model, import_model


def export_related_records(parent_model, child_model, relation_field, parent_fields=None, child_fields=None, filter_domain=None, limit=1000, export_path=None):
    """
    Wrapper around dynamic_data_tool.export_rel.
    """
    class Args:
        pass
    args = Args()
    args.parent_model = parent_model
    args.child_model = child_model
    args.relation_field = relation_field
    args.parent_fields = parent_fields
    args.child_fields = child_fields
    args.domain = filter_domain
    args.output = export_path
    args.limit = limit
    export_rel(args)
    return {
        "success": True,
        "parent_model": parent_model,
        "child_model": child_model,
        "export_path": export_path
    }


def import_related_records(parent_model, child_model, relation_field, parent_fields=None, child_fields=None, input_path=None, name_prefix=None):
    """
    Wrapper around dynamic_data_tool.import_rel.
    """
    class Args:
        pass
    args = Args()
    args.parent_model = parent_model
    args.child_model = child_model
    args.relation_field = relation_field
    args.parent_fields = parent_fields
    args.child_fields = child_fields
    args.input = input_path
    args.name_prefix = name_prefix
    import_rel(args)
    return {
        "success": True,
        "parent_model": parent_model,
        "child_model": child_model
    }


def export_records(model_name, output_path, filter_domain=None):
    """
    Wrapper around dynamic_data_tool.export_model.
    """
    class Args:
        pass
    args = Args()
    args.model = model_name
    args.output = output_path
    export_model(args)
    return {
        "success": True,
        "model_name": model_name,
        "export_path": output_path
    }


def import_records(import_path, model_name, field_mapping=None, create_if_not_exists=True, update_if_exists=True):
    """
    Wrapper around dynamic_data_tool.import_model.
    """
    class Args:
        pass
    args = Args()
    args.model = model_name
    args.input = import_path
    args.name_prefix = None
    import_model(args)
    return {
        "success": True,
        "model_name": model_name,
        "import_path": import_path
    }
