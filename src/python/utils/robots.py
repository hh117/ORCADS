import os,yaml

def load_robots(robot_dir):
    robots = []

    for robot_def in os.listdir(robot_dir):
        if robot_def.endswith('yaml'):
            robot = yaml.safe_load(open(os.path.join(robot_dir,robot_def), 'r').read())
            robots.append(robot)

    return robots

def get_robot(robot_id,robot_db):

    for robot in robot_db:
        if robot['id'] == robot_id:
            return robot

    return None