export function post(url, data = {}) {
  const postData = {
    csrf_token: UiContext.csrf_token,
    ...data,
  };
  return $.ajax({
    url,
    method: 'post',
    dataType: 'json',
    data: postData,
  });
}
