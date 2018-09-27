import os,yaml

def load_environment(env_dir):

    env = []

    for item_file in os.listdir(env_dir):
        if item_file.endswith('yaml'):
            item = yaml.safe_load(open(os.path.join(env_dir,item_file), 'r').read())
            env.append(item)

    return env

def find_obj_env(obj_id,env):
    '''
    Returns item based on the id
    :param obj_id:
    :param env:
    :return:
    '''

    for obj in env:
        if obj['id'] == obj_id:
            return obj

    return None