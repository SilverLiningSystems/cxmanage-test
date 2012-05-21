#!/bin/env python

""" This class encapsulates the user interface for the calxeda firmware
    update tool prototype. """

from cxfwupd_resources import cxfwupd_resources

class ui:
    def __init__(self, controller):
        self._controller = controller
        
    @staticmethod
    def _print(strlist):
        for str in strlist:
            print str,
        print

    @staticmethod
    def _get_menu_sel(prompt):
        return ui._get_int(prompt)

    @staticmethod
    def _get_int(prompt):
        inp = ui._get_str(prompt)
        intval = -1
        if (len(inp)):
            try:
                intval = int(inp)
            except ValueError:
                pass
        return intval

    @staticmethod
    def _get_str(prompt):
        if prompt:
            ui._print([prompt])
        return raw_input()

    @staticmethod
    def _is_yes(yn):
        return yn in cxfwupd_resources.get_yes_strings();

    def display_mainmenu(self):
        """ Display the main menu, along with some status information about
        each menu item."""
        strings = cxfwupd_resources.get_strings('main-menu')
        while True:
            # FIXME: all the accessors need to move to the controller
            mss = self._controller.get_setting_str('tftp')
            iss = self._controller.get_setting_str('images')
            tss = self._controller.get_setting_str('targets')
            pss = self._controller.get_setting_str('plans-cnt')
            vss = self._controller.get_setting_str('plans-valid-cnt')
            ess = self._controller.get_setting_str('plans-exec-cnt')
            sss = self._controller.get_setting_str('plans-status-cnt')
            self._print([strings['menu-title']])
            self._print([])
            self._print(['1.',
                         strings['tftp-option'],
                         strings['tftp-status'].format(mss)])
            self._print(['2.',
                         strings['images-option'],
                         strings['images-status'].format(iss)])
            self._print(['3.',
                         strings['targets-option'], '\n  ',
                         strings['targets-status'].format(tss)])
            self._print(['4.',
                         strings['plan-option'],
                         strings['plan-status'].format(pss)])
            self._print(['5.',
                         strings['validate-option'],
                         strings['validate-status'].format(vss)])
            self._print(['6.',
                         strings['execute-option'],
                         strings['execute-status'].format(ess)])
            self._print(['7.',
                         strings['status-option'], '\n  ',
                         strings['status-status'].format(sss)])
            self._print(['8.',
                         strings['exit-option'],
                         ''])
            self._print([])
            self._print([strings['main-prompt']])
            menusel = ui._get_menu_sel(None)
            if menusel == 1:
                self.handle_tftp_options()
            elif menusel == 2:
                self.handle_images_options()
            elif menusel == 3:
                self.handle_targets_options()
            elif menusel == 4:
                self.handle_plan_options()
            elif menusel == 5:
                self.handle_validation_options()
            elif menusel == 6:
                self.handle_execute_options()
            elif menusel == 7:
                self.handle_status_options()
            elif menusel == 8:
                # At this point we may want to make sure that the user
                # really wants to exit and understands the consequences.
                break;
            else:
                self._print(['XXX  error  XXX. Enter a value from 1 to 8.'])

    def handle_tftp_options(self):
        """ Handle the main menu option to work with tftp settings by
        presenting a tftp options menu. """
        strings = cxfwupd_resources.get_tftp_strings()
        # Display TFTP menu
        # If the current state is 
        #    No TFTP server set
        #       1. Create and use an internal tftp server
        #       2. Specify a tftp server IP address and port
        #       3. Exit, leaving no tftp server chosen
        #    Internal tftp server set
        #       1. Set internal tftp server on another interface
        #       2. Specify a tftp server IP address and port
        #       3. Exit, leaving internal tftp selected
        #    tftp IP and port set
        #       1. Create and use an internal tftp server
        #       2. Specify a different IP address and/or port
        #       3. Exit leaving server unchanged
        self._print([strings['tftp-options'], '\n'])
        self._print([self._controller.get_setting_report('tftp'), '\n'])
        self._print(['1.', strings['set-new-tftp']])
        tftp_status = self._controller.get_status_code('tftp-selection');
        if tftp_status == 0:  # No tftp server set
            self._print(['1.', strings['create-and-use']])
            self._print(['2.', strings['specify-tftp']])
            self._print(['3.', strings['exit-no-server']])
        elif tftp_status == 1:  # Internal tftp server set
            self._print(['1.', strings['change-interface']])
            self._print(['2.', strings['specify-tftp']])
            self._print(['3.', strings['exit-internal-sel']])
        else: # External tftp server set
            self._print(['1.', strings['create-and-use']])
            self._print(['2.', strings['different-address']])
            self._print(['3.', strings['exit-server-sel']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            if tftp_status == 2:
                self.handle_tftp_interface_change()
            else:
                self.handle_create_internal_tftp()
        elif menusel == 2:
            if tftp_status == 3:
                self.handle_tftp_addr_change()
            else:
                self.handle_specify_tftp_server()

    #
    # I'm sure I don't have all the use cases down for images.
    # To create a plan, we have to pair up a tftp server path for an
    # image with one or more targets.  If the tftp server is local,
    # we can populate the list of possible images by looking in
    # one or more directories specified by the user; but if it's remote,
    # the user has to tell use the whole path for each image.
    #
    # To add a new image to the ftp repository, the user has to give us
    # a local path, and we'll try to copy it do a tftp location
    # he specifies (using tftp if the server is not local).  The tftp server
    # at a remote site may not have write access to the path specified.
    #
    # Our job in the ui is to keep the model informed of all images we
    # know about, and
    #     what type it is
    #     what path the target should request
    #     whether it's been verified
    #     the last time we know it was successfully accessed
    #     whether it was there the last time we checked.
    def handle_images_options(self):
        """ Handle the main menu images option by presenting a menu of image
        editing options."""
        strings = cxfwupd_resources.get_strings('image-menu')
        # Image options:
        #  1. List images
        #  2. Add an image
        #  3. Delete an image
        #  4. Validate an image
        #  5. Exit images menu
        self._print([strings['image-options']])
        self._print(['1.', strings['list-images']])
        self._print(['2.', strings['add-image']])
        self._print(['3.', strings['delete-image']])
        self._print(['4.', strings['validate-image']])
        self._print(['5.', strings['exit']])
        strings = cxfwupd_resources.get_strings('image-menu')
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_images()
        elif menusel == 2:
            self.handle_add_image()
        elif menusel == 3:
            self.handle_delete_image()
        elif menusel == 4:
            self.handle_validate_image()


    def handle_targets_options(self):
        """ Handle the main menu targets option by presenting a menu of target
        editing options."""
        strings = cxfwupd_resources.get_strings('targets-menu')
        # Image options:
        #  1. List Calxeda server groups
        #  2. Add new Calxeda servers group
        #  3. Remove a server group
        #  4. Edit a server group
        #  4. Exit this menu.
        self._print([strings['targets-options'], '\n'])
        self._print(['1.', strings['list-targets']])
        self._print(['2.', strings['add-targets']])
        self._print(['3.', strings['remove-targets']])
        self._print(['4.', strings['edit-targets']])
        self._print(['5.', strings['exit']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_target_groups()
        elif menusel == 2:
            self.handle_add_target_group()
        elif menusel == 3:
            self.handle_remove_target_group()
        elif menusel == 4:
            self.handle_edit_target_group()

    def handle_plan_options(self):
        """ Handle the main menu plans option by presenting a menu of plan
        editing options."""
        strings = cxfwupd_resources.get_strings('plans-menu')
        # Firmware update plan options:
        #   1. List update plans
        #   2. Add a plan
        #   3. Edit a plan
        #   4. Delete a plan
        #   5. Exit this menu.
        self._print([strings['plans-options'], '\n'])
        self._print(['1.', strings['list-plans']])
        self._print(['2.', strings['add-plan']])
        self._print(['3.', strings['edit-plan']])
        self._print(['4.', strings['delete-plan']])
        self._print(['5.', strings['exit']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_plans('all')
        elif menusel == 2:
            self.handle_add_plan()
        elif menusel == 3:
            self.handle_edit_plan()
        elif menusel == 4:
            self.handle_delete_plan()

    def handle_validation_options(self):
        """ Handle the main menu plan validation option by presenting
        a menu of further options."""
        strings = cxfwupd_resources.get_strings('validation-menu')
        # Plan validation options:
        #  1. List plan validation status
        #  2. Validate or re-validate a plan
        #  3. Exit
        self._print([strings['validation-options'], '\n'])
        self._print(['1.', strings['list-plans']])
        self._print(['2.', strings['validate-plan']])
        self._print(['3.', strings['exit']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_plans('status')
        elif menusel == 2:
            self.handle_validate_plan()

    def handle_execute_options(self):
        """ Handle the main menu plan execution option by presenting
        a menu of further options."""
        strings = cxfwupd_resources.get_strings('execution-menu')
        # Firmware update plan execution options:
        #    1. List plans available for execution.
        #    2. Start executing a plan.
        #    3. Exit without executing a plan
        self._print([strings['execution-options'], '\n'])
        self._print(['1.', strings['list-plans']])
        self._print(['2.', strings['execute-plan']])
        self._print(['3.', strings['exit']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_plans('all')
        elif menusel == 2:
            self.handle_execute_plan()

    def handle_status_options(self):
        """ Handle the main menu plan status option by presenting
        a menu of further options."""
        strings = cxfwupd_resources.get_strings('plan-status-menu')
        # Plan execution status options:
        #   1. View started plans
        #   2. View plans that have started and completed
        #   3. View plans that have started and are still executing
        #   4. Cancel an executing plan
        #   5. Exit
        self._print([strings['status-options'], '\n'])
        self._print(['1.', strings['list-started']])
        self._print(['2.', strings['list-done']])
        self._print(['3.', strings['list-execing']])
        self._print(['4.', strings['cancel-plan']])
        self._print(['5.', strings['exit']])
        self._print([strings['option-prompt']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_list_plans('started')
        elif menusel == 2:
            self.handle_list_plans('done')
        elif menusel == 3:
            self.handle_list_plans('execing')
        elif menusel == 4:
            self.handle_cancel_plan()


    def _handle_internal_tftp(self, interface, port, rootdir):
        strings = cxfwupd_resources.get_strings('tftp-interface-menu')
        # Change internal tftp server interface:
        #    Internal tftp server is currently listening on ethx port y
        #    Enter new interface:
        #    Enter new port
        #    Apply changes?
        self._print([strings['status'] % [interface, port, rootdir]])
        interface = ui._get_str(strings['change-interface'])
        port = ui._get_int(strings['change-port'])
        rootdir = ui._get_str(strings['change-rootdir'])
        self._print([strings['status'] % [interface, port, rootdir]])
        yn = ui._get_str(strings['apply-changes'])
        if ui._is_yes(yn):
            self._controller.set_internal_tftp_server(interface, port, rootdir)
            return True
        else:
            self._print(['leave-unchanged'])
            return False

    def handle_tftp_interface_change(self):
        #FIXME: Don't allow this if there are plans still executing using
        #the intenal TFTP server.
        interface = self._controller.get_internal_tftp_interface()
        port = self._controller.get_internal_tftp_port()
        rootdir = self._controller.get_internal_tftp_root()
        if self._handle_internal_tftp(interface, port, rootdir):
            self._controller.restart_tftp_server()

    def handle_create_internal_tftp(self):
        self._handle_internal_tftp('eth0', 69, '/tftpboot')

    def handle_tftp_addr_change(self):
        addr = self._controller.get_external_tftp_addr()
        port = self._controller.get_external_tftp_port()
        self._handle_external_tftp(addr, port)

    def _handle_external_tftp(self, addr, port):
        strings = cxfwupd_resources.get_strings('tftp-external-menu')
        # Change configured tftp server
        #    External tftp server is at xx.yy.zz.00 listening on port xx
        #    Enter new tftp server address.
        #    Enter port
        #    Apply changes?
        self._print([strings['status'] % [addr, port]])
        addr = ui._get_str(strings['change-addr'])
        port = ui._get_int(strings['change-port'])
        self._print([strings['status'] % [addr, port]])
        yn = ui._get_str(strings['apply-changes'])
        if ui._is_yes(yn):
            self._controller.set_external_tftp_server(addr, port)
            return True
        else:
            self._print(['leave-unchanged'])
            return False

    def handle_specify_tftp_server(self):
        # Specify a tftp server
        #    There is currently no tftp server configured
        #    Specify tftp server ip address
        self._handle_tftp_addr_change('127.0.0.1', 69)

    def handle_list_images(self):
        self._controller.list_images('all')
            
    def handle_add_image(self):
        strings = cxfwupd_resources.get_strings('image-strings')
        # Adding an image
        #   1. Transfer an image on local disk to the tftp server
        #   2. Add a reference to an image already on the tftp server
        #   3. Exit
        self._print([strings['adding']])
        self._print(['1.', strings['add-from-local']])
        self._print(['2.', strings['add-remote']])
        self._print(['3.', strings['exit']])
        menusel = ui._get_menu_sel(strings['option-prompt'])
        if menusel == 1:
            self.handle_add_local_image(strings)
        elif menusel == 2:
            self.handle_add_remote_image(strings)

    def handle_put_image_on_tftp(self, f):
        pass

    def handle_image_upload(self, f, really_upload):
        if self._controller.validate_image_file(f):
            self._print([strings['image validated'],
                         self._controller.get_image_header_str(f)])
            if really_upload:
                self.handle_put_image_on_tftp(localpath)
            # FIXME: add to model

    def handle_add_local_image(self, strings):
        # Enter path:
        localpath = ui._get_str(strings['enter-local-path'])
        try:
            f = open(localpath)
            if f:
                handle_image_upload(f, True)
                f.close()
        except IOError:
            self._print(['File', localpath, 'could not be accessed.'])
            return
        
    def handle_add_remote_image(self, strings):
        tftppath = ui._get_str(strings['enter-tftp-path'])
        localpath = self._controller.tftp_get(tftppath)
        try:
            f = open(localpath)
            if f:
                handle_image_upload(f, False)
                f.close()
        except IOError:
            yn = ui._get_str(strings['nf-add-anyway'])
            if ui._is_yes(yn):
                # FIXME: get metadata
                # FIXME: add to model
                pass
        except TypeError:
            pass

    def handle_delete_image(self):
        if self._controller.get_status_code('tftp-selection') == 1:
            pass # remove the file from the local tftp server's file system
        else:
            self._print(['This function is not implemented.\n',
                         'Delete images manually at the tftp server.'])
            
    def handle_validate_image(self):
        # tftp the image, check its header
        pass

    def handle_list_target_groups(self):
        self._controller.list_target_groups('all')

    def handle_add_target_group(self):
        # Name the target group:
        # 1. Add targets from a range of IP addresses
        # 2. Add targets for Calxeda servers in a fabric
        pass

    def handle_remove_target_group(self):
        # Select the target group to delete:
        pass

    def handle_edit_target_group(self):
        # Select the target group
        # 1. Add servers to the group
        # 2. Remove servers from the group
        pass

    def handle_add_plan(self):
        # Name the plan:
        # Enter an initial list of target addresses by range or fabric or groups
        # Enter a list of images
        # Set a schedule (number of updates to start at once, deley between groups)
        pass

    def handle_edit_plan(self):
        # 1. Change plan target list
        # 2. Change plan image list
        # 3. Change plan schedule
        pass

    def handle_delete_plan(self):
        # Select a plan for deletion
        pass

    def handle_validate_plan(self):
        # Select a plan for validation
        pass

    def handle_execute_plan(self):
        pass

    def handle_list_plans(self, status):
        pass

    def handle_cancel_plan(self):
        pass
