import unittest,sys
from pathlib import Path
from email.message import EmailMessage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from services import parse_shipment
class ShippingRevisionTests(unittest.TestCase):
 def html(self,subject,url):
  m=EmailMessage();m['Subject']=subject;m['From']='orders@example.com';m.set_content('Your order is on its way.');m.add_alternative('<a href="'+url+'">Track package</a>',subtype='html');return m.as_bytes()
 def test_multipart_tracking_in_link(self):
  rows=parse_shipment(self.html('Your order is on its way','https://www.ups.com/track?tracknum=1Z999AA10123456784'),strict=True)
  self.assertEqual(rows[0]['carrier'],'UPS');self.assertEqual(rows[0]['status'],'In transit')
 def test_html_tracking_when_plain_part_has_no_details(self):
  m=EmailMessage();m['Subject']='Order update';m.set_content('View HTML for details');m.add_alternative('<p>Your package shipped. Tracking: 1Z999AA10123456784</p>',subtype='html')
  self.assertEqual(len(parse_shipment(m.as_bytes(),strict=True)),1)
 def test_wrapped_carrier_link_decoded_without_request(self):
  url='https://mail.example/click?url=https%3A%2F%2Fwww.ups.com%2Ftrack%3Ftracknum%3D1Z999AA10123456784'
  self.assertEqual(len(parse_shipment(self.html('Your package shipped',url),strict=True)),1)
 def test_usps_link(self):
  rows=parse_shipment(self.html('Your package shipped','https://tools.usps.com/go/TrackConfirmAction?tLabels=9400111899223856928499'),strict=True)
  self.assertEqual(rows[0]['number'],'9400111899223856928499')
 def test_lookalike_host_rejected(self):
  self.assertEqual(parse_shipment(self.html('Your package shipped','https://ups.com.evil.example/track?tracknum=1Z999AA10123456784'),strict=True),[])
 def test_dhl_link(self):
  rows=parse_shipment(self.html('Your order dispatched','https://www.dhl.com/global-en/home/tracking.html?tracking-id=1234567890'),strict=True)
  self.assertEqual(rows[0]['carrier'],'DHL')
 def test_promotional_link_rejected(self):
  self.assertEqual(parse_shipment(self.html('Free shipping sale','https://www.ups.com/track?tracknum=1Z999AA10123456784'),strict=True),[])
if __name__=='__main__':unittest.main()
