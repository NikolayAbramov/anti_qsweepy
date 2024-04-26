from ui_generator import UiGenerator
from ui_callbacks import UiCallbacks
from feedback_processor import FeedbackProcessor
from hw_control_process import hw_process
from config_handler import ConfigHandler
import data_structures as ds
from nicegui import ui
import multiprocessing as mp


if __name__ == "__main__":
    q_command = mp.Queue(maxsize=100)
    q_feedback = mp.Queue(maxsize=100)

    ui_objects = ds.UiObjects()
    conf_h = ConfigHandler(ui_objects)
    conf_h.load_config()

    ui_cb = UiCallbacks(ui_objects, conf_h, q_command)
    ui_gen = UiGenerator(ui_objects, ui_cb, conf_h)
    fp = FeedbackProcessor(q_feedback, q_command, ui_objects, ui_cb)

    ui_gen.create_ui()

    #mp.set_start_method('fork')
    p = mp.Process(target=hw_process, args=(q_command, q_feedback))
    p.start()
    ui.timer(0.01, fp.check_queue)

    ui_cb.connect_devices()
    ui.timer(0.1, ui_cb.request_vna_data)
    
    ui.run( port=ui_objects.tcp_ip_port, reload=False)
    q_command.put({'op':'terminate'})
    p.join()