import base64 from 'base-64';
import Clipboard from 'clipboard';

import { NamedPage } from 'vj/misc/PageLoader';
import substitute from 'vj/utils/substitute';
import Notification from 'vj/components/notification';
import i18n from 'vj/utils/i18n';

const page = new NamedPage('user_detail', async () => {
  $('[name="profile_contact_copy"]').get().forEach((el) => {
    const data = $(el).attr('data-content');
    const decoded = base64.decode(data);
    const clip = new Clipboard(el, { text: () => decoded });
    clip.on('success', () => {
      Notification.success(substitute(i18n('"{data}" copied to clipboard!'), { data: decoded }), 2000);
    });
    clip.on('error', () => {
      Notification.error(substitute(i18n('Copy "{data}" failed :('), { data: decoded }));
    });
  });
});

export default page;
