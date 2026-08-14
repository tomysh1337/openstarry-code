from __future__ import annotations

from types import SimpleNamespace

import pytest

from openstarry_code.gateway.channel_notices import channel_notice_locale, render_channel_notice


@pytest.mark.parametrize(
    ("locale", "required", "approved"),
    [
        (
            "en",
            "Access approval is required. Pairing request: PAIR1234. "
            "Ask an OpenStarry Code operator to approve it before sending another message.",
            "Access approved. Send a message to start chatting.",
        ),
        (
            "zh-Hans",
            "需要访问审批。配对申请：PAIR1234。请联系 OpenStarry Code 操作员批准后再发送消息。",
            "访问已获批准。请发送一条消息以开始对话。",
        ),
        (
            "ja",
            "アクセスの承認が必要です。ペアリング リクエスト: PAIR1234。"
            "別のメッセージを送る前に、OpenStarry Code のオペレーターに承認を依頼してください。",
            "アクセスが承認されました。メッセージを送信して会話を開始してください。",
        ),
        (
            "fr",
            "Une approbation d'accès est requise. Demande d'appairage : PAIR1234. "
            "Demandez à un opérateur OpenStarry Code de l'approuver avant d'envoyer un autre message.",
            "Accès approuvé. Envoyez un message pour commencer à discuter.",
        ),
        (
            "de",
            "Eine Zugriffsfreigabe ist erforderlich. Kopplungsanfrage: PAIR1234. "
            "Bitten Sie einen OpenStarry Code-Operator, sie zu genehmigen, bevor Sie eine "
            "weitere Nachricht senden.",
            "Zugriff genehmigt. Senden Sie eine Nachricht, um den Chat zu beginnen.",
        ),
        (
            "es",
            "Se requiere aprobación de acceso. Solicitud de emparejamiento: PAIR1234. "
            "Pide a un operador de OpenStarry Code que la apruebe antes de enviar otro mensaje.",
            "Acceso aprobado. Envía un mensaje para empezar a chatear.",
        ),
    ],
)
def test_channel_notices_use_each_supported_gateway_locale(
    locale: str,
    required: str,
    approved: str,
) -> None:
    config = SimpleNamespace(control_ui=SimpleNamespace(default_locale=locale))

    assert channel_notice_locale(config) == locale
    assert (
        render_channel_notice("pairing_required", config=config, pairing_code="PAIR1234")
        == required
    )
    assert render_channel_notice("pairing_approved", config=config) == approved


@pytest.mark.parametrize(
    "config",
    [
        None,
        SimpleNamespace(),
        SimpleNamespace(control_ui=SimpleNamespace(default_locale="ko")),
        SimpleNamespace(control_ui=SimpleNamespace(default_locale=object())),
    ],
)
def test_channel_notice_locale_falls_back_to_english(config: object | None) -> None:
    assert channel_notice_locale(config) == "en"
    assert render_channel_notice("pairing_approved", config=config) == (
        "Access approved. Send a message to start chatting."
    )
