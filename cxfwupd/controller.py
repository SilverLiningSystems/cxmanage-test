""" The controller object mediates between a UI and the application model.
In this case, the controller understands the model's container structure
and the objects it contains: tftp, images, targets and plans. """

from model import model

class controller:

    def __init__(self, model):
        self._model = model

    def get_setting_report(self, subject):
        """ Various objects can have extended reports as well as
            status strings. """
        #FIXME
        return self.get_setting_str(subject)

    def get_setting_str(self, subject):
        """ Various objects in the model can report their status as a
        string.  This method invokes those reports for subjects it
        recognizes. """
        s = ''
        if subject == 'tftp':
            s = self._model._tftp.get_settings_str()
        elif subject == 'images':
            s = self._model._images.get_settings_str()
        elif subject == 'targets':
            s = self._model._targets.get_settings_str()
        elif subject == 'plans-cnt':
            s = self._model._plans.get_count_str()
        elif subject == 'plans-valid-cnt':
            s = self._model._plans.get_validate_status_str()
        elif subject == 'plans-exec-cnt':
            s = self._model._plans.get_executing_count_str()
        elif subject == 'plans-status-cnt':
            s = self._model._plans.get_status_count_str()
        else:
            s = "No report found."
        return s

    def get_status_code(self, subject):
        """ Various objects in the model have state that can be summarized
        in an integer code.  This method discovers and encodes those
        states. """
        code = -1
        if subject == 'tftp-selection':
            if not self._model._tftp._ipaddr:
                code = 0 # No tftp server set
            else:
                if self._model._tftp._isinternal:
                    code = 1
                else:
                    code = 2
        return code

###########################  TFTP-specific methods ###########################

    def set_internal_tftp_server(self, interface, port):
        pass

    def get_internal_tftp_interface(self):
        #FIXME
        return 'eth0'

    def get_internal_tftp_port(self):
        #FIXME
        return 69

    def restart_tftp_server(self):
        pass

    def get_external_tftp_addr(self):
        #FIXME
        return '127.0.0.1'

    def get_external_tftp_port(self):
        #FIXME
        return 69

    def set_external_tftp_server(self, addr, port):
        pass

###########################  Images-specific methods ###########################

    def list_images(self, subject):
        pass


###########################  Targets-specific methods #########################

    def list_target_groups(self, subject):
        pass
