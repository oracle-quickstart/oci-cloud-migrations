resource "oci_artifacts_container_repository" "terminate_nat_gateway" {
  compartment_id = var.compartment_ocid
  display_name   = "terminate_nat_gateway"
  is_public      = "false"
}

locals {
  ocir_docker_repository = join("", [lower(data.oci_identity_region_subscriptions.region_subscriptions.region_subscriptions[0].region_key), ".ocir.io"])
}

resource "null_resource" "docker_login" {
  depends_on = [oci_artifacts_container_repository.terminate_nat_gateway]
  triggers = {
    terminate_nat_gateway_function_version             = var.terminate_nat_gateway_function_version
  }
  provisioner "local-exec" {
    command = "echo '${var.ocir_password}' |  docker login ${local.ocir_docker_repository} --username ${data.oci_objectstorage_namespace.tenancy_namespace.namespace}/${var.ocir_user_name} --password-stdin"
  }
}

resource "null_resource" "terminate_nat_gateway_fn_setup" {

  depends_on = [null_resource.docker_login]
  triggers = {
    function_version = var.terminate_nat_gateway_function_version
  }

  provisioner "local-exec" {
    command     = "image=$(docker images | grep terminate_nat_gateway | awk -F ' ' '{print $3}') ; docker rmi -f $image &> /dev/null ; echo $image"
    working_dir = "terminate_nat_gateway_function"
  }

  provisioner "local-exec" {
    command     = "fn build"
    working_dir = "terminate_nat_gateway_function"
  }
  provisioner "local-exec" {
    command     = "image=$(docker images | grep terminate_nat_gateway | grep ${var.terminate_nat_gateway_function_version} | awk -F ' ' '{print $3}') ; docker tag $image ${local.ocir_docker_repository}/${data.oci_objectstorage_namespace.tenancy_namespace.namespace}/terminate_nat_gateway:${var.terminate_nat_gateway_function_version}"
    working_dir = "terminate_nat_gateway_function"
  }

  provisioner "local-exec" {
    command     = "docker push ${local.ocir_docker_repository}/${data.oci_objectstorage_namespace.tenancy_namespace.namespace}/terminate_nat_gateway:${var.terminate_nat_gateway_function_version}"
    working_dir = "terminate_nat_gateway_function"
  }

}