'''
Written by Mengzhan Liufu at Yu Lab, the University of Chicago
'''
from trodes_connection import subscribe_to_data, connect_to_trodes
# from data_buffering import data_buffering
from detector import Detector
import threading
import multiprocessing as mp
import argparse
import json
from collections import deque


def detection_task(
    detector_name, 
    detector_param, 
    shared_data_buffer, 
    trodes_hardware
    ):
    # Create detector
    detector = Detector(
        detector_name,
        shared_data_buffer,
        detector_param['statescript_fxn_num'],
        trodes_hardware,
        window_size = detector_param['window_size'],
        target_lowcut = detector_param['target_lowcut'],
        target_highcut = detector_param['target_highcut'],
        target_phase = detector_param['target_phase']
    )
    detection_thread = threading.Thread(target=detector.closed_loop_stim)
    detection_thread.start()
    # detection_thread.join()


def buffering_task(
        lfp_client, 
        shared_data_buffer, 
        target_channel, 
        # buffer_lock
    ):
    while True:
        # with buffer_lock:
        current_data = lfp_client.receive()['lfpData']
        shared_data_buffer.append(current_data[target_channel])


if __name__ == "__main__":
    # Parse command-line argument
    parser = argparse.ArgumentParser(description='CLC real-time stim parameters')
    parser.add_argument('--params', default=None, type=str, help='Path to JSON parameter file')
    args = parser.parse_args()

    # Load JSON data from the provided file path
    with open(args.params, 'r') as file:
        params = json.load(file)

    # ------------------------- trodes connection -------------------------
    server_address = params['server_address']
    lfp_client, trodes_hardware, _, _ = connect_to_trodes(
        server_address,
        20,
        'lfp'
    )

    # ------------------------- Create and initialize shared data buffer -------------------------
    shared_data_buffer = deque([], maxlen=params['data_buffer_size'])
    # buffer_lock = threading.Lock()
    for i in range(params['data_buffer_size']):
        current_sample = lfp_client.receive()
        current_data = current_sample['lfpData']
        shared_data_buffer.append(current_data[params['target_channel']])

    # ------------------------- Start buffering data -------------------------
    buffering_thread = threading.Thread(
        target=buffering_task, 
        args=(
            lfp_client, 
            shared_data_buffer, 
            params['target_channel'], 
            # buffer_lock
        )
    )
    buffering_thread.start()

    # ------------------------- Spawn detector processes -------------------------
    # detection_process_lst = []
    for detector_name, detector_param in params['detector_params'].items():

        assert detector_param['window_size'] <= params['data_buffer_size'], (
            'Detector input window size must be smaller than data buffer size'
        )

        new_detection_process = mp.Process(
            target=detection_task,
            args=(
                detector_name,
                detector_param,
                shared_data_buffer,
                trodes_hardware
            )
        )
        new_detection_process.start()
        # detection_process_lst.append(new_detection_process)

    # # Wait for all processes to complete
    # for p in detection_process_lst:
    #     p.join()

    # # Ensure buffering thread is stopped gracefully (optional)
    # buffering_thread.join()


