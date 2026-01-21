"""
Invoice Extractors
==================
Auto-register extractors

Author: BotV3
Version: 3.0.0
"""

import logging

logger = logging.getLogger(__name__)

# Import extractors ตามลำดับความสำคัญ
# Extractor ที่เฉพาะเจาะจงต้องอยู่ก่อน
from .customs_department import CustomsDepartmentExtractor
from .kln_seaport import KLNSeaportExtractor
from .eastern_sea_lamchabang_terminal import EasternSeaLamchabangTerminalExtractor
from .lcmt import LCMTExtractor
from .ngow_hok import NgowHokExtractor
from .siam_commercial_seaport import SiamCommercialSeaportExtractor
from .tips import TIPSExtractor
from .ck_line import CKLineExtractor
from .ck_line_thailand import CKLineThailandExtractor
from .shanghai_jinjiang_shipping import ShanghaiJinjiangShippingExtractor
from .jinjiang_shipping_agency import JinjiangShippingAgencyExtractor
from .exclusive_global_logistics import ExclusiveGlobalLogisticsExtractor
from .hutchison_laemchabang_terminal import HutchisonLaemchabangTerminalExtractor
from .grab import GrabExtractor
from .kasikorn_bank import KasikornBankExtractor
from .union_world_shipping import UnionWorldShippingExtractor
from .laem_chabang_international_terminal import LaemChabangInternationalTerminalExtractor
from .evergreen_container_terminal import EvergreenContainerTerminalExtractor
from .evergreen_marine import EvergreenMarineExtractor
from .cosco_shipping_lines import CoscoShippingLinesExtractor
from .rcl_feeder import RCLFeederExtractor
from .myorder_intelligence import MyOrderIntelligenceExtractor
from .marvel_vision import MarvelVisionExtractor
from .thailand_post import ThailandPostExtractor
from .starline_agencies import StarlineAgenciesExtractor
from .benline_agencies import BenlineAgenciesExtractor
from .maersk_line import MaerskLineExtractor
from .sim_thailand import SimThailandExtractor
from .sitc_container_lines import SITCContainerLinesExtractor
from .dongjin_shipping import DongjinShippingExtractor
from .awot_global_logistics import AWOTGlobalLogisticsExtractor
from .ksher_payment import KsherPaymentExtractor
from .punthai_coffee import PunthaiCoffeeExtractor
from .omise import OmiseExtractor
from .thai_happy_logistics import ThaiHappyLogisticsExtractor
from .tiktok_shop import TikTokShopExtractor
from .beam_data import BeamDataExtractor
from .lcb_container_terminal import LCBContainerTerminalExtractor
from .wan_hai_lines import WanHaiLinesExtractor
from .cma_cgm_asia_shipping import CMACGMAsiaShippingExtractor
from .ocean_network_express import OceanNetworkExpressExtractor
from .ts_container_lines import TSContainerLinesExtractor
from .cenoagent_thai import CenoagentThaiExtractor
from .oocl_thailand import OOCLThailandExtractor
from .yang_ming_line import YangMingLineExtractor
from .cu_lines import CULinesExtractor
from .mst import MSTInvoiceExtractor
from .msc import MSCInvoiceExtractor

# List extractors ตามลำดับความสำคัญ
# Extractor ที่เฉพาะเจาะจงต้องอยู่ก่อน
EXTRACTORS = [
    CustomsDepartmentExtractor(),  # กรมศุลกากร ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    KLNSeaportExtractor(),  # KLN Seaport ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    EasternSeaLamchabangTerminalExtractor(),  # Eastern Sea Lamchabang Terminal ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    LCMTExtractor(),  # LCMT ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    NgowHokExtractor(),  # Ngow Hok ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    SiamCommercialSeaportExtractor(),  # Siam Commercial Seaport ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    TIPSExtractor(),  # TIPS ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    CKLineExtractor(),  # CK Line ต้องอยู่ก่อนเพราะเฉพาะเจาะจง (มี Tax ID ชัดเจน)
    CKLineThailandExtractor(),  # CK Line (Thailand) ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    ShanghaiJinjiangShippingExtractor(),  # SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD. ต้องอยู่ก่อน JinjiangShippingAgency เพราะเฉพาะเจาะจงกว่า
    JinjiangShippingAgencyExtractor(),  # Jinjiang Shipping Agency ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    ExclusiveGlobalLogisticsExtractor(),  # Exclusive Global Logistics ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    HutchisonLaemchabangTerminalExtractor(),  # Hutchison Laemchabang Terminal ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    LaemChabangInternationalTerminalExtractor(),  # Laem Chabang International Terminal ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    GrabExtractor(),  # Grab ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    KasikornBankExtractor(),  # Kasikorn Bank ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    UnionWorldShippingExtractor(),  # Union World Shipping ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    EvergreenContainerTerminalExtractor(),  # Evergreen Container Terminal ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    EvergreenMarineExtractor(),  # Evergreen Marine ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    CoscoShippingLinesExtractor(),  # COSCO Shipping Lines ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    RCLFeederExtractor(),  # RCL Feeder ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    MyOrderIntelligenceExtractor(),  # MyOrder Intelligence ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    MarvelVisionExtractor(),  # Marvel Vision ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    ThailandPostExtractor(),  # Thailand Post ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    StarlineAgenciesExtractor(),  # Starline Agencies ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    BenlineAgenciesExtractor(),  # Benline Agencies ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    MaerskLineExtractor(),  # Maersk Line ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    SimThailandExtractor(),  # SIM Thailand ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    SITCContainerLinesExtractor(),  # SITC Container Lines ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    DongjinShippingExtractor(),  # DONGJIN SHIPPING ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    AWOTGlobalLogisticsExtractor(),  # AWOT Global Logistics ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    KsherPaymentExtractor(),  # Ksher Payment Co., Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    PunthaiCoffeeExtractor(),  # Punthai Coffee Co., Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    OmiseExtractor(),  # Omise Company Limited ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    ThaiHappyLogisticsExtractor(),  # Thai Happy Logistics Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    TikTokShopExtractor(),  # TikTok Shop (Thailand) Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    BeamDataExtractor(),  # Beam Data Co., Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    LCBContainerTerminalExtractor(),  # LCB Container Terminal 1 Ltd. ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    WanHaiLinesExtractor(),  # WAN HAI LINES ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    CMACGMAsiaShippingExtractor(),  # CMA CGM Asia Shipping ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    OceanNetworkExpressExtractor(),  # Ocean Network Express ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    TSContainerLinesExtractor(),  # TS Container Lines ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    CenoagentThaiExtractor(),  # Cenoagent Thai ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    OOCLThailandExtractor(),  # OOCL Thailand ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    YangMingLineExtractor(),  # Yang Ming Line ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    CULinesExtractor(),  # CU Lines ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
    MSTInvoiceExtractor(),  # MST ต้องอยู่ก่อน MSC เพราะเฉพาะเจาะจงกว่า
    MSCInvoiceExtractor(),  # MSC อยู่ท้ายสุดเพราะเป็น fallback
]

__all__ = [
    'EXTRACTORS',
    'CustomsDepartmentExtractor',
    'KLNSeaportExtractor',
    'EasternSeaLamchabangTerminalExtractor',
    'LCMTExtractor',
    'NgowHokExtractor',
    'SiamCommercialSeaportExtractor',
    'TIPSExtractor',
    'CKLineExtractor',
    'CKLineThailandExtractor',
    'ShanghaiJinjiangShippingExtractor',
    'JinjiangShippingAgencyExtractor',
    'ExclusiveGlobalLogisticsExtractor',
    'HutchisonLaemchabangTerminalExtractor',
    'LaemChabangInternationalTerminalExtractor',
    'GrabExtractor',
    'KasikornBankExtractor',
    'UnionWorldShippingExtractor',
    'EvergreenContainerTerminalExtractor',
    'EvergreenMarineExtractor',
    'CoscoShippingLinesExtractor',
    'RCLFeederExtractor',
    'MyOrderIntelligenceExtractor',
    'MarvelVisionExtractor',
    'ThailandPostExtractor',
    'StarlineAgenciesExtractor',
    'BenlineAgenciesExtractor',
    'MaerskLineExtractor',
    'SimThailandExtractor',
    'SITCContainerLinesExtractor',
    'DongjinShippingExtractor',
    'AWOTGlobalLogisticsExtractor',
    'KsherPaymentExtractor',
    'PunthaiCoffeeExtractor',
    'OmiseExtractor',
    'ThaiHappyLogisticsExtractor',
    'TikTokShopExtractor',
    'BeamDataExtractor',
    'LCBContainerTerminalExtractor',
    'WanHaiLinesExtractor',
    'CMACGMAsiaShippingExtractor',
    'OceanNetworkExpressExtractor',
    'TSContainerLinesExtractor',
    'CenoagentThaiExtractor',
    'OOCLThailandExtractor',
    'YangMingLineExtractor',
    'CULinesExtractor',
    'MSTInvoiceExtractor',
    'MSCInvoiceExtractor',
]
