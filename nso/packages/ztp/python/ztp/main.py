# -*- mode: python; python-indent: 4 -*-
import ncs,_ncs
from ncs.application import Service
import ncs.experimental
from ncs.dp import Action
import ncs.maapi as maapi
import ncs.maagic as maagic
from _ncs import dp
import socket
import datetime
from _ncs import dp

# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class GetDay0(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
	
	device_serial = kp[0][0].as_pyval()

        with maapi.single_write_trans(uinfo.username, "system", db=ncs.RUNNING) as th:
            root = maagic.get_root(th)
            ztp = root.ztp[device_serial]
	    filename = ztp.day0
	    ip = ztp.ip
	    hostname = ztp.hostname
        
        f = open("/opt/ncs-run/packages/ztp/day0_templates/{}".format(filename), "r")
        day0 = f.read()
        f.close()
        
        # replacing values in the template
        day0 = day0.replace("${IP}", ip)
        day0 = day0.replace("${HOSTNAME}", hostname)
        day0 = day0.replace("${SERIAL}", device_serial)
        
        output.message = day0

class Onboard(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):

        device_serial=kp[0][0].as_pyval()

        with maapi.single_write_trans(uinfo.username, "system", db=ncs.RUNNING) as th:
            self.log.info("Onboarding ztp device: %s" % (kp))
            root = maagic.get_root(th)
            device=root.ztp[device_serial]
            ztp_template_vars = ncs.template.Variables()
            ztp_template_template = ncs.template.Template(device)
            ztp_template_vars.add('DEVICE_NAME', device_serial)
            ztp_template_vars.add('ADDRESS', device.ip)
            ztp_template_template.apply('ztp-template', ztp_template_vars)
            th.apply()

        with maapi.single_read_trans(uinfo.username, "system", db=ncs.OPERATIONAL) as th:
            root = maagic.get_root(th)
            inputs = root.devices.device[device_serial].ssh.fetch_host_keys.get_input()
            self.log.info(root.devices.device[device_serial].ssh.fetch_host_keys(inputs))
            self.log.info(root.devices.device[device_serial].sync_from())

	#send notif
 	csocket = socket.socket()
        try:
            ctx = dp.init_daemon('send-notif')
            # making a control socket
            dp.connect(dx=ctx, sock=csocket, type=dp.CONTROL_SOCKET, ip='127.0.0.1', port=_ncs.PORT)
            # getting all the required hashes
            ns_hash = _ncs.str2hash("http://example.com/ztp")
            # notif_name_hash = _ncs.str2hash('service-name')
            notif_state_hash = _ncs.str2hash('state')
            notif_device_hash = _ncs.str2hash('device')
	    notif_hash = _ncs.str2hash('ztp-status')
            
            # making the notification
            message = []
            message += [_ncs.TagValue(_ncs.XmlTag(ns_hash, notif_hash),
                                      _ncs.Value((notif_hash, ns_hash), _ncs.C_XMLBEGIN))]
            message += [_ncs.TagValue(ncs.XmlTag(ns_hash, notif_state_hash),
                                      _ncs.Value("ready"))]
            message += [_ncs.TagValue(ncs.XmlTag(ns_hash, notif_device_hash),
                                      _ncs.Value(device_serial))]
            message += [_ncs.TagValue(_ncs.XmlTag(ns_hash, notif_hash),
                                      _ncs.Value((notif_hash, ns_hash), _ncs.C_XMLEND))]
            # registering the stream
            livectx = dp.register_notification_stream(ctx, None, csocket, "ztp")
            # time
            now = datetime.datetime.now()
            time = _ncs.DateTime(now.year, now.month, now.day, now.hour, now.minute,
                                 now.second, now.microsecond, now.timetz().hour,
                                 now.timetz().minute)
            # sending the notification
            dp.notification_send(livectx, time, message)
            self.log.info(message)
            self.log.info("ZTP: Onboarding notification has been generated.")
        except Exception as e:
            self.log.info("ZTP: Exception : " + e.message)
        finally:
            csocket.close()



        output.message = "OK"
# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_action('get_day0-actionpoint',GetDay0 )
        self.register_action('onboard-actionpoint',Onboard )

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
