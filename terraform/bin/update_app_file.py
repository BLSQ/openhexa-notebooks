import sys
import yaml

terraform_output_file_path = sys.argv[1]
config_file_path = sys.argv[2]
HEXA_NOTEBOOKS_PROXY_HTTP_LETSENCRYPT_CONTACT_EMAIL = "pvanliefland@bluesquarehub.com"
HEXA_NOTEBOOKS_IMAGE_NAME = "blsq/openhexa-base-notebook" 
HEXA_NOTEBOOKS_IMAGE_TAG = "0.1.2"
HEXA_APP_DOMAIN = "app.test.openhexa.org"

print(f"Config Map using Terraform output")

# Open & load the terraform output file to fetch relevant project config values
with open(terraform_output_file_path, "r") as terraform_output_file:
    terraform_output = yaml.load(terraform_output_file, Loader=yaml.FullLoader)

    # Open and load the project config file and update it with the values from the terraform output
    with open(config_file_path, "r+") as project_config_file:
        config = yaml.load(project_config_file, Loader=yaml.FullLoader)
        config["proxy"]["secretToken"] = terraform_output.get("HEXA_NOTEBOOKS_PROXY_SECRET_TOKEN")
        config["proxy"]["service"]["loadBalancerIP"] = terraform_output.get("gcp_compute_address")
        config["proxy"]["https"]["hosts"][0] = terraform_output.get("aws_route53_record_name")
        config["proxy"]["https"]["letsencrypt"]["contactEmail"] = HEXA_NOTEBOOKS_PROXY_HTTP_LETSENCRYPT_CONTACT_EMAIL


        config["hub"]["cookieSecret"] = terraform_output.get("HEXA_NOTEBOOKS_HUB_COOKIE_SECRET")
        config["hub"]["db"]["url"] = f"postgresql://{terraform_output.get('gcp_sql_database_user')}:{terraform_output.get('gcp_sql_database_password')}@127.0.0.1:5432/{terraform_output.get('gcp_sql_database_name')}"
        config["hub"]["extraContainers"][0]["command"][2]= f"-instances={terraform_output.get('CLOUDSQL_CONNECTION_STRING')}=tcp:5432"
        config["hub"]["extraEnv"]["APP_URL"] = f"https://{HEXA_APP_DOMAIN}"
        config["hub"]["extraEnv"]["APP_CREDENTIALS_URL"] = f"https://{HEXA_APP_DOMAIN}/notebooks/credentials/"
        config["hub"]["extraEnv"]["CONTENT_SECURITY_POLICY"] = f"frame-ancestors 'self' {HEXA_APP_DOMAIN};"

        config["singleuser"]["extraEnv"]["CONTENT_SECURITY_POLICY"] = f"frame-ancestors 'self' {HEXA_APP_DOMAIN};"
        config["singleuser"]["image"]["name"] = HEXA_NOTEBOOKS_IMAGE_NAME
        config["singleuser"]["image"]["tag"] = HEXA_NOTEBOOKS_IMAGE_TAG

        # Write back the updated file data to disk
        # (We need to truncate the file first, as we want to overwrite its content with the updated config)
        project_config_file.seek(0)
        project_config_file.truncate()
        project_config_file.write(
            yaml.dump(
                config,
                default_flow_style=False,
                sort_keys=False,
            )
        )

        print("Successfully extracted terraform output and updated app.yaml")
