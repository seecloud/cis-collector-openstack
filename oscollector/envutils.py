import os
import exception


def fake_get_creds_from_env_vars():
    """
    Hardcoded credentials for test Devstack environment
    :return creds: dict with access credentials
    """
    creds = {
        'controller_ip': '192.168.122.4',
        'username': 'admin',
        'password': 'msa',
        'project_name': 'admin',
        'user_domain_id': 'default',
        'project_domain_id': 'default'
    }
    return creds


def get_creds_from_env_vars():
    """
    Load environment variables with access credentials,
    OpenStack configuration and SSL certificates information

    :return creds: dict with access credentials and OpenStack configuration
    """

    required_env_vars = ["OS_CONTROLLER_IP", "OS_USERNAME", "OS_PASSWORD"]
    missing_env_vars = [v for v in required_env_vars if v not in os.environ]
    if missing_env_vars:
        msg = ("The following environment variables are "
               "required but not set: %s" % " ".join(missing_env_vars))
        raise Exception(msg)

    creds = {
        'controller_ip': os.environ.get("OS_CONTROLLER_IP"),
        'username': os.environ.get("OS_USERNAME"),
        'password': os.environ.get("OS_PASSWORD"),
        'project_name': get_project_name_from_env(),
        'user_domain_id': os.environ.get("OS_USER_DOMAIN_ID"),
        'project_domain_id': os.environ.get("OS_PROJECT_DOMAIN_ID"),
    }

    return creds


def get_project_name_from_env():
    """Return project or tenant name from environment variable

    :return tenant_name: project or tenant name
    """

    tenant_name = os.environ.get("OS_PROJECT_NAME",
                                 os.environ.get("OS_TENANT_NAME"))
    if tenant_name is None:
        raise exception.ValidationError("Either the OS_PROJECT_NAME or "
                                        "OS_TENANT_NAME environment variable "
                                        "is required, but neither is set.")

    return tenant_name


def get_endpoint_type_from_env():
    """Return endpoint_type from environment variable

    :return endpoint_type: endpoint_type
    """

    endpoint_type = os.environ.get("OS_ENDPOINT_TYPE",
                                   os.environ.get("OS_INTERFACE"))
    if endpoint_type and "URL" in endpoint_type:
        endpoint_type = endpoint_type.replace("URL", "")

    return endpoint_type
