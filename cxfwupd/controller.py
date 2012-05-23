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

    def tftp_get(self, tftppath, localpath):
        #FIXME
        return None

###########################  Images-specific methods ###########################

    def list_images(self, subject):
        #FIXME
        return ''

    def validate_image_file(self, f):
        #FIXME
        return False

    def get_image_header_str(self, f):
        #FIXME
        return ''

    def add_image(image_type):
        pass

###########################  Targets-specific methods #########################

    def list_target_groups(self, subject):
        """ Return a formatted listing of target groups """
        pass

    def add_targets_to_group(self, group, targets):
        """ Add the targets to the list of targets for the group.
        Eliminate duplicates."""
        pass

    def delete_target_group(self, group):
        pass

    def get_targets_in_range(self, startaddr, endaddr):
        """ Attempt to reach a socman on each of the addresses in the range.
        Return a list of socman addresses successfully reached. """
        pass

    def get_targets_from_fabric(self, nodeaddr):
        """ Attempt to get the addresses of socman instances that are known
        to the ipmi server at 'nodeaddr'.  If nodeaddr is a socman image,
        it will know about the instances that are part of fabric that
        nodeaddr\'s node belongs to.  Return a list of addresses reported."""
        pass

    def target_group_exists(self, grpname):
        """ Return true if the grpname is the name of a target group contained
        in the model."""
        #FIXME
        return False
 ########################    Plans-specific methods     ######################
    def list_plans(self, subject):
        """ Return a formatted list of plan names """
