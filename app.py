import time
import os

from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

fleetdm_url = "https://fleetdm.example.com"
token=os.environ['CREDENTIALS_DIRECTORY'] + '/checkmy-token'
with open(token, "r") as f:
    api_token = f.read().replace('\n', ' ')
# ip_address = "172.30.128.95"#"10.0.2.15"  # Замените на нужный IP хоста

critical_list = [45, 46, 47, 48, 1, 15, 49, 50, 51, 52, 53, 54, 55, 56]

# Заголовки для аутентификации
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

def find_host_by_ip_fallback(search_ip):
    """
    Ищет хост с указанным IP-адресом в массиве объектов hosts.

    :param search_ip: IP-адрес для поиска (строка)
    :return: Объект хоста (словарь) или None, если не найден
    """
    host_url = f"{fleetdm_url}/api/latest/fleet/hosts"
    response = requests.get(host_url, headers=headers)
    if response.status_code == 200:
        for host in response.json().get('hosts',[]):
            if host.get("primary_ip") == search_ip or host.get("public_ip") == search_ip:
                return host
    return None


# Получить хост по IP


def get_host_by_ip(ip):
    host_url = f"{fleetdm_url}/api/latest/fleet/hosts?query={ip}"
    response = requests.get(host_url, headers=headers)

    if response.status_code == 200:
        hosts = response.json().get('hosts', [])

        if len(hosts) > 0:
            # ищем в листе хост со статусом online и возвращаем его
            online_hosts = [h for h in hosts if h.get('status') == 'online']
            if len(online_hosts) > 0:
                return online_hosts[0]
            else:
                # Если хостов онлайн не нашлось - возвращаем первый найденный хост
                return hosts[0]
        else:
            fallback_host=find_host_by_ip_fallback(ip)
            if fallback_host is not None:
                return fallback_host
    return None

# Получить подробности о хосте и его политике

def get_host_policies(host_id):
    host_details_url = f"{fleetdm_url}/api/latest/fleet/hosts/{host_id}"
    response = requests.get(host_details_url, headers=headers)
    if response.status_code == 200:
        policies = response.json().get('host', {}).get('policies', [])
        critical_policies = [p for p in policies if p['id'] in critical_list]
        non_critical_policies = [p for p in policies if p['id'] not in critical_list]
        return critical_policies, non_critical_policies
    return [], []

# Проверяем информацию о хосте пока не получим refetch_requested = false


def wait_for_refetch(host_id):
    refetch_url = f"{fleetdm_url}/api/latest/fleet/hosts/{host_id}/refetch"
    # Просим FleetDM обновить информацию о хосте
    response = requests.post(refetch_url, headers=headers)
    for _ in range(20):
        host_details_url = f"{fleetdm_url}/api/latest/fleet/hosts/{host_id}"
        response = requests.get(host_details_url, headers=headers)
        # print(response.json())
        if response.status_code == 200:
            if not response.json().get('host', {}).get("refetch_requested"):
                policies = response.json().get('host', {}).get('policies', [])
                critical_policies = [p for p in policies if p['id'] in critical_list]
                non_critical_policies = [p for p in policies if p['id'] not in critical_list]
                return critical_policies, non_critical_policies
            else:
                time.sleep(1)
                print(_)

        else:
            return [], []
    return [], []


# Основная страница



@app.route('/')
def index():
#    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)[0]

    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip_address = request.remote_addr


    # ip_address = '172.30.129.139'
    host = get_host_by_ip(ip_address)
    print("Host:" + str(host))
    if not host:
        return render_template('update.html',
                               device_found=False,
                               access_granted=1,
                               client_ip=ip_address,
                               )
        # return "Host not found", 404
    if host['status'] == 'offline':
        print("OFFLINE!!!!")

        return render_template('update.html',
                               device_found=False,
                               access_granted=0,
                               client_ip=ip_address,
                               device_offline=host['seen_time'],
                               host_name=host['hostname'],
                               platform=host['platform'],
                               host_uuid=host['uuid'],
                               )



    critical_policies, non_critical_policies = get_host_policies(host['id'])
    return render_template('update.html',
                           critical_policies=critical_policies,
                           non_critical_policies=non_critical_policies,
                           access_granted= sum(1 for p in critical_policies if p['response'] == 'fail'),
                           failed_policies=[p for p in critical_policies if p['response'] == 'fail'],
                           host_name=host['hostname'],
                           platform=host['platform'],
                           host_uuid=host['uuid'],
                           device_found=True
                           )

# Маршрут для асинхронного обновления политик


@app.route('/update-policies', methods=['GET'])
def update_policies():
 #   ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip_address = request.remote_addr
    # ip_address = '172.30.129.139'
    host = get_host_by_ip(ip_address)
    if not host:
        return jsonify({'error': 'Host not found',
                        'device_found': False,
                        'access_granted': 1}), 404

    critical_policies, non_critical_policies = wait_for_refetch(host['id'])

    # Если хост оффлайн:
    if host['status'] == 'offline':
        return jsonify({'error': 'Device is offline',
                        'device_found': False,
                        'device_offline': host['seen_time'],
                        'host_name': host['hostname'],
                        'host_uuid': host['uuid'],
                        'platform': host['platform'],
                        'access_granted': 0}), 404

    return jsonify({'critical_policies': critical_policies,
                    'non_critical_policies': non_critical_policies,
                    'failed_policies':[p for p in critical_policies if p['response'] == 'fail'],
                    'access_granted': sum(1 for p in critical_policies if p['response'] == 'fail'),
                    'platform': host['platform'],
                    'device_found': True
                    })


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
