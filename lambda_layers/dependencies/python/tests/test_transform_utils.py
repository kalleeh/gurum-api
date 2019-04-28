
my_dict = {}
my_dict['DesiredCount'] = None
my_dict['HealthCheckPath'] = '/health'
my_dict['DockerImage'] = None

my_dict['Priority'] = '1'
my_dict['Listener'] = 'arn:aws:elasticloadbalancing:eu-west-1:123456789012:listener/app/gureume-platform/1968bab4f7a51062/09c1ab82befe95d8'
my_dict['GroupName'] = 'team1'

print(json.dumps(dict_to_kv(my_dict, 'ParameterKey', 'ParameterValue', clean=True)))