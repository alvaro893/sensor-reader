import SerialCommunication as serial
import Analisys
import HttpConnection
import lowCamera

__author__ = 'Alvaro'

network_thread = HttpConnection.NetworkThread()
analysis_thread = Analisys.AsyncAnalysis(lowCamera.frame_arr)



def frame_jobs(raw_frame):
    network_thread.add_to_buffer(raw_frame)
    processed_frame = lowCamera.process_frame(raw_frame)
    analysis_thread.put_arr_in_queue(processed_frame)

serial.start(frame_jobs)  # this blocks

network_thread.stop
analysis_thread.stop
