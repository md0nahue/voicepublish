defmodule VoiceWeb.ErrorJSONTest do
  use VoiceWeb.ConnCase, async: true

  test "renders 404" do
    assert VoiceWeb.ErrorJSON.render("404.json", %{}) == %{errors: %{detail: "Not Found"}}
  end

  test "renders 500" do
    assert VoiceWeb.ErrorJSON.render("500.json", %{}) ==
             %{errors: %{detail: "Internal Server Error"}}
  end
end
