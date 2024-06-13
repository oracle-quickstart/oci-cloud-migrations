import oci
from fdk import response
import io
import json
import logging
import logging.handlers
import logging.config

def handler(ctx, data: io.BytesIO=None):
    func_name = ctx.FnName()
    global logger
    logger = logging.getLogger(func_name)
    logger.setLevel(logging.INFO)
    logger.info("Function started.")

    try:
        cfg = ctx.Config()
    except Exception:
        logger.error("Missing function parameters.")
        raise
    try:
        body = json.loads(data.getvalue())
        route_table_id = body["data"]["resourceId"]
        terminate_nat_gateway(route_table_id=route_table_id)
    except (Exception) as ex:
        logger.error("Function error: " + ex)
        raise

    logger.info("Function complete.")
    return response.Response(
        ctx,
        response_data=json.dumps(body),
        headers={"Content-Type": "application/json"}
    )

def terminate_nat_gateway (route_table_id):
    signer = oci.auth.signers.get_resource_principals_signer()
    vcn_client = oci.core.VirtualNetworkClient(config={}, signer=signer)
    logger.info("Starting route table modification.")
    vcn_response = vcn_client.get_route_table(rt_id=route_table_id)
    route_table=vcn_response.data
    route_rules=vcn_response.data.route_rules

    new_route_rules = []
    nat_gateway_id = "none"

    logger.info("Looking for NAT Gateway routes.")
    for route_rule in route_rules:
        if route_rule.network_entity_id.find("natgateway") == -1: 
            new_route_rules.append(route_rule)
        else:
            logger.info("Found NAT Gateway route.")
            nat_gateway_id = route_rule.network_entity_id

    route_table_update = oci.core.models.UpdateRouteTableDetails(
        defined_tags=route_table.defined_tags,
        display_name=route_table.display_name,
        freeform_tags=route_table.freeform_tags,
        route_rules=new_route_rules    
    )
    if nat_gateway_id != "none":
        logger.info("Removing NAT Gateway routes.")
        vcn_client.update_route_table(route_table_id, route_table_update)
        logger.info("Removing NAT Gateway.")
        vcn_client.delete_nat_gateway(nat_gateway_id)
    else:
        logger.info("No NAT Gateway routes found.")
    logger.info("Complete route table modification.")