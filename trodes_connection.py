"""""""""
Written by Mengzhan Liufu at Yu Lab, University of Chicago
"""""""""

from trodesnetwork import trodes
from trodesnetwork import socket


def call_statescript(hardware, function_num):
    """
    Call a ECU StateScript method of index function_num

    :param hardware: trodes.hardware object
    :param function_num: the index of StateScript funciton defined in Trodes

    :return message: the message sent from trodes (unpacked by msgpack.unpackb) to see if the calling is successful
    """
    message = hardware.ecu_shortcut_message(function_num)
    return message


def connect_to_trodes(local_server_address, count_per_lfp, data_type):
    """
    Connect python client to trodes server, get socket subscriber, info requester and
    hardware objects; sampling rate and period

    :param local_server_address: the tcp address of trodes server
    :param count_per_lfp: for how many samples one lfp package is sent
    :param data_type: lfp, spikes, camera, or dio

    :return: lfp subscriber object, trodes_hardware, info requester, sampling rate
    """
    client = subscribe_to_data(data_type, local_server_address)
    info = get_trodes_info(local_server_address)
    hardware = get_trodes_hardware(local_server_address)
    info = get_trodes_info(local_server_address)
    sampling_rate = info.request_timerate() / count_per_lfp

    return client, hardware, info, sampling_rate


def subscribe_to_data(data_type, local_server_address):
    """
    Return a trodes.socket subscriber to data_type data

    :param local_server_address: tcp server address of trodes
    :param data_type: lfp, spikes or dio data

    :return: socket subscriber object
    :rtype: object
    """
    rtn = None
    if data_type == 'lfp' or data_type == 'LFP':
        rtn = socket.SourceSubscriber('source.lfp', server_address=local_server_address)
    if data_type == 'spikes' or data_type == 'Spikes':
        rtn = socket.SourceSubscriber('source.spikes', server_address=local_server_address)
    if data_type == 'digital' or data_type == 'Digital':
        rtn = socket.SourceSubscriber('source.digital', server_address=local_server_address)
    if data_type == 'neural' or data_type == 'Neural':
        rtn = socket.SourceSubscriber('source.neural', server_address=local_server_address)
    if data_type == 'camera' or data_type == 'Camera':
        rtn = socket.SourceSubscriber('source.position', server_address=local_server_address)

    if not rtn:
        print('Data type not found')

    return rtn


def get_trodes_info(local_server_address):
    """
    Return a trodes info requester object

    :param local_server_address:

    :return: TrodesInfoRequester Object
    :rtype: object
    """
    return trodes.TrodesInfoRequester(server_address=local_server_address)


def get_trodes_hardware(local_server_address):
    """
    Return a trodes hardware object

    :param local_server_address:

    :return: TrodesHardware Object
    :rtype: object
    """
    return trodes.TrodesHardware(server_address=local_server_address)