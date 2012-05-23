#!/bin/env python

""" This class mediates access to resource strings, mainly for purposes of
internationalization.  It's probably going to remain just a namespace, with
all static methods. I don't know whether that's considered good python or
not."""

class cxfwupd_resources:

    @staticmethod
    def _get_resource(yamlfile, entry):
        return None

    @staticmethod
    def get_strings(subject):
        """ This resource is a multi-entry dictionary. The indexes are
        subject areas.
        Each value is a dictionary of strings, indexed by a menu-item id.
        The resource is optionally in a YAML file.
        If the YAML file isn't found, a hard-coded dictionary is returned. """
        menu = cxfwupd_resources._get_resource('cxfwupd_resources.yaml',
                                              subject)
        if not menu:
            allstrings = {
                'response-strings':
                    {
                    'yes': ['y', 'Y', 'yes', 'Yes', 'YES'],
                    'no':  ['n', 'N', 'no', 'No', 'NO']
                    },
                'main-menu':
                    {
                    'menu-title': 'Calxeda Firmware Update Workflow',
                    'main-prompt': 'Enter a command: ',
                    'tftp-option': 'Specify or set up a tftp server',
                    'tftp-status': '(Current settings: {0})',
                    'images-option': 'Marshall and check firmware images',
                    'images-status': '(Current settings: {0})',
                    'targets-option':
                        'Specify or discover, and group target Calxeda servers',
                    'targets-status': '(Current settings: {0})',
                    'plan-option': 'Create or review a distribution plan.\n  ',
                    'plan-status': '({0} plans currently stored)',
                    'validate-option': 'Validate a plan',
                    'validate-status': '{0}',
                    'execute-option': 'Execute a plan.\n  ',
                    'execute-status': '(Currently {0} plans in execution)',
                    'status-option': 'Check the status of a distribition plan',
                    'status-status':
                        '(Currently {0} plans have status information)',
                    'exit-option': 'Exit this shell.'
                    },
                'tftp':
                    {
                    'not-set': 'Not set',
                    'internal-server': ' The internal server.',
                    'is-reachable': ' Is reachable.',
                    'known-good-once': ' Known good at one time, but not now.',
                    'not-reachable': ' Not reachable.',
                    'tftp-options': 'tftp Options',
                    'set-new-tftp': 'Set a new tftp server.',
                    'create-and-use': 'Create and use a temporary tftp server.',
                    'specify-tftp': 'Specify a tftp server IP address and port.',
                    'change-interface': 'Set internal tftp server on another interface.',
                    'different-address': 'Specify a different IP address and/or port',
                    'exit-no-server': 'Exit with no tftp server chosen.',
                    'exit-internal-sel': 'Exit leaving internal tftp selected on the current port.',
                    'exit-server-sel': 'Exit leaving server unchanged.',
                    'option-prompt': 'Enter tftp editing option:'
                    },
                'image-menu':
                    {
                    'image-options': 'Deployable Firmware Image Options:',
                    'base-dirs': 'Specify base directories.',
                    'list-images': 'List firmware images',
                    'add-image': 'Add a firmware image',
                    'delete-image': 'Delete a firmware image',
                    'validate-image': 'Validate an image',
                    'exit': 'Exit this menu.',
                    'option-prompt': 'Enter an option:'
                    },
                'targets-menu':
                    {
                    'targets-options': 'Options for finding systems to update',
                    'list-targets': 'List Calxeda server groups.',
                    'add-targets': 'Add a new Calxeda server group.',
                    'remove-targets': 'Remove a server group from the list',
                    'edit-targets': 'Edit a server group',
                    'exit': 'Exit this menu.',
                    'option-prompt': 'Enter an option:'
                    },
                'plans-menu':
                    {
                    'plans-options': 'Firmware update plan options:',
                    'list-plans': 'List update plans',
                    'add-plan': 'Add a plan',
                    'edit-plan': 'Edit a plan',
                    'delete-plan': 'Delete a plan',
                    'exit': 'Exit this menu.',
                    'option-prompt': 'Enter a plan option.'
                    },
                'validation-menu':
                    {
                    'validation-options': 'Plan validation options',
                    'list-plans': 'List plan validation status',
                    'validate-plan': 'Validate or re-validate a plan',
                    'exit': 'Exit',
                    'option-prompt': 'Enter a validation option.'
                    },
                'execution-menu':
                    {
                    'execution-options': 'Firmware update plan execution options:',
                    'list-plans': 'List plans available for execution',
                    'execute-plan': 'Start executing a plan',
                    'exit': 'Exit without executing a plan',
                    'option-prompt': 'Enter an execution option'
                    },
                'plan-status-menu':
                    {
                    'status-options': 'Plan execution status options:',
                    'list-started': 'List started plans',
                    'list-done': 'LIst plans that have started and finished',
                    'list-execing': 'List plans that have started and are still executing',
                    'cancel-plan': 'Cancel an executing plan',
                    'exit': 'Exit',
                    'option-prompt': 'Enter an option'
                    },
                'tftp-interface-menu':
                    {
                    'interface-change-options': 'Change internal tftp server interface:',
                    'status': '(Internal tftp server is current listening on {0}, port {1} {2})',
                    'change-interface': 'Enter new network interface (i.e. ethx)',
                    'change-port': 'Enter new listener port',
                    'apply-changes': 'Apply changes',
                    'exit': 'Exit.',
                    'leave-unchanged': 'Leaving internal tftp interface and port unchanged'
                    },
                'tftp-external-menu':
                    {
                    'status': '(External tftp server is at {0} listening on port {1}',
                    'change-addr': 'Enter new IP address:',
                    'change-port': 'Enter new listener port:',
                    'change-rootdir': 'Enter tftp root directory:',
                    'apply-changes': 'Apply changes to external tftp server address and port?',
                    'leave-unchanged': 'Leaving external tftp server and port unchanged'
                    },
                'image-strings':
                    {
                    'adding': 'Adding an image',
                    'exit': 'Exit without doing anything',
                    'add-from-local': 'Transfer an image on local disk to the tftp server',
                    'add-remote': 'Add a reference to an image already on the tftp server',
                    'option-prompt': 'Enter an option:',
                    'enter-local-path': 'Enter local path:',
                    'enter-tftp-path': 'Enter file name on the tftp server:',
                    'nf-add-anyway': 'Remote file not found.  Add anyway?',
                    'image-validated': 'Image validated.'
                    },
                'imagetype-menu':
                    {
                    'select': 'Select an image type:',
                    'socman': 'ECME controller image',
                    'uboot': 'uboot image',
                    'bootloader': 'ECME bootloader image',
                    'dtb': 'Device Tree Blob'
                    },
                'validate-image-menu':
                    {
                    'options': 'Validate an image:',
                    'local': 'Validate an image stored locally',
                    'remote': 'Validate an image stored on the tftp server',
                    'exit': 'Exit.',
                    'prompt': 'Enter an option:',
                    'local-path': 'Enter the path of the local file:',
                    'remote-path': 'Enter the path of the file on the tftp server:',
                    'remote-file-not-found': 'File not found on tftp server',
                    'local-file-not-found': 'File not found',
                    'not-valid-image': 'The file does not contain a valid image'
                    },
                'target-strings':
                    {
                    'existing-groups': 'Existing target groups:',
                    'enter-new-name': 'Enter the new group name:',
                    'enter-del-name': 'Enter the name of the group to delete:',
                    'enter-edit-name': 'Enter the name of a group to edit:',
                    'add-from-range': 'Add targets from a range of IP addresses',
                    'add-fabric': 'Add targets for Calxeda servers in a fabric',
                    'add-individual': 'Add individual targets',
                    'exit': 'Exit',
                    'prompt': 'Enter the source of target addresses:',
                    'successful-delete': 'Group was successfully deleted',
                    'not-deleted': 'The group was not deleted.',
                    'add-servers': 'Add servers to the group',
                    'remove-servers': 'Remove servers from the group',
                    'edit-metadata': 'Edit metadata',
                    'group-exists': 'Target group name already exists',
                    'group-not-found': 'There is no target group with that name',
                    'edit-prompt': 'Enter an edit option:'
                    },
                'plan-strings':
                    {
                    'existing-plans': 'Existing plans:',
                    'enter-new-name': 'Enter a name for the new plan:'
                    }
            }
            menu = allstrings[subject]
        return menu;

    @staticmethod
    def get_tftp_strings():
        return cxfwupd_resources.get_strings('tftp')

    @staticmethod
    def get_main_menu_strings():
        return cxfwupd_resources.get_strings('main-menu')

    @staticmethod
    def get_yes_strings():
        return ui.get_resource('response-strings')['yes']
