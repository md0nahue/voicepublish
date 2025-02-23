defmodule VoiceWeb.AudioChannel do
  use VoiceWeb, :channel

  def join("audio:stream", _payload, socket) do
    {:ok, socket}
  end

  def handle_in("new_chunk", %{"data" => data_chunk}, socket) do
    ExAws.S3.initiate_multipart_upload("your-bucket", "your-object-key")
    |> ExAws.request()
    |> case do
      {:ok, upload} ->
        part = ExAws.S3.upload_part("your-bucket", "your-object-key", upload.upload_id, 1, data_chunk)
        |> ExAws.request()
        ExAws.S3.complete_multipart_upload("your-bucket", "your-object-key", upload.upload_id, [part])
        |> ExAws.request()
        {:noreply, socket}
      {:error, reason} ->
        IO.inspect(reason)
        {:stop, :error, socket}
    end
  end
end
