# MD_FS.py
import streamlit as st
import pandas as pd
import io, re, random
import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
# ───────────────────────────────────────────────────
# 1) 유저가 수정·확장 가능한 영역:
#    – 기본 target_products(재고명→무게 매핑)
#    – box_limit(박스 최대 용량)
# ───────────────────────────────────────────────────
target_products={
    "[동해 콘서트MD_Alive] 볼캡" : 750,
    "[동해 콘서트MD_Alive] 티셔츠" : 750,
    "[동해 콘서트MD_Alive] 페이퍼 인센스" : 100,
    "[온유_FLOW] 스티커 팩" : 300,
    "[온유_FLOW] 아크릴 키링 - YELLOW" : 300,
    "[온유_FLOW] 아크릴 키링 - PURPLE" : 300,
    "[온유_FLOW] 아크릴 키링 - PINK" : 300,
    "[온유_FLOW] 스티커 세트" : 200,
    "[DPR_Artist Merch] ARTIC_Kinema Ballcap" : 1000,
    "[DPR_Artist Merch] ARTIC_Kinema Keyring" : 300,
    "[DPR_Artist Merch] CREAM_psyche: red T-Shirt / White" : 1250,
    "[DPR_Artist Merch] CREAM_psyche: red T-Shirt / Black" : 1250,
    "[DPR_Artist Merch] ARTIC_Kinema T-Shirt / White" : 1250,
    "[DPR_Artist Merch] ARTIC_Kinema T-Shirt / Black" : 1250,
    "[DPR_Artist Merch] CREAM_psyche: red Ballcap" : 1000,
    "[DPR_Artist Merch] IAN_MIITO T-Shirt_Red / Size 1" : 1250,
    "[DPR_Artist Merch] IAN_MIITO T-Shirt_Red / Size 3" : 1250,
    "[DPR_Artist Merch] IAN_MIITO T-Shirt_Red / Size 2" : 1250,
    "[DPR_Artist Merch] IAN_✚Ian Damage T-Shirt / Size 1" : 1250,
    "[DPR_Artist Merch] IAN_✚Ian Damage T-Shirt / Size 2" : 1250,
    "[DPR_Artist Merch] IAN_✚Ian Damage T-Shirt / Size 3" : 1250,
    "[DPR_Artist Merch] IAN_INSANITY T-Shirt / Size 1" : 1250,
    "[DPR_Artist Merch] IAN_INSANITY T-Shirt / Size 2" : 1250,
    "[DPR_Artist Merch] IAN_INSANITY T-Shirt / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_Black / Size 1" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_Black / Size 2" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_Black / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_Black / Size 4" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_White / Size 1" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_White / Size 2" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_White / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn T-Shirt_White / Size 4" : 1250,
    "[DPR_Artist Merch] CREAM_psyche: red Earring" : 500,
    "[DPR_Tour Merch] Dpr Tank Top_Black / Size 1" : 1000,
    "[DPR_Tour Merch] Dpr Tank Top_Black / Size 2" : 1000,
    "[DPR_Tour Merch] Dpr Tank Top_White / Size 1" : 1000,
    "[DPR_Tour Merch] Dpr Tank Top_White / Size 2" : 1000,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Black / Size 1" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Black / Size 2" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Black / Size 3" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Gray / Size 1" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Gray / Size 2" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Hoodie_Gray / Size 3" : 1875,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Red / Size 1" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Red / Size 2" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Red / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Blue / Size 1" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Blue / Size 2" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Blue / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Gold / Size 1" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Gold / Size 2" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Crop T-Shirt_Gold / Size 3" : 1250,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Black / Size 1" : 750,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Black / Size 2" : 750,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Black / Size 3" : 750,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Gray / Size 1" : 750,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Gray / Size 2" : 750,
    "[DPR_Tour Merch] The Dream Reborn Shorts_Gray / Size 3" : 750,
    "[DPR_Tour Merch] The Dream Reborn Trucker Cap" : 1000,
    "[DPR_Tour Merch] DPR Socks / Size 1" : 500,
    "[DPR_Tour Merch] DPR Socks / Size 2" : 500,
    "[DPR_Tour Merch] The Dream Rebborn Pop Grip" : 300,
    "[DPR_2024 SEASONS MERCH] DREAM LIGHT_Standard version" : 2500,
    "[온유_FLOW] 스마트톡 - RABBIT VER" : 200,
    "[온유_FLOW] 스마트톡 - HEART VER" : 200,
    "[온유_FLOW] 담요" : 2000,
    "[온유_FLOW] 미니 포스터 - BEAT VER" : 1000,
    "[온유_FLOW] 미니 포스터 - DRUM VER" : 1000,
    "[ONEW FLOW] 머그컵" : 500,
    "[온유_FLOW] 펜 메모패드 세트" : 300,
    "[온유_FLOW] 트레이딩 포토카드" : 200,
    "[온유_FLOW] 리유저블 백" : 1000,
    "[온유_FLOW] 러그" : 2000,
    "[비투비 공식 응원봉v3 상시 판매] 비투비 응원봉" : 3750,
    "[김재중 2025 시즌그리팅] 시즌그리팅" : 1250,
    "[김재중 아시아 투어MD_J-PARTY] 아크릴 코스터" : 400,
    "[김재중 아시아 투어MD_J-PARTY] 핀브로치" : 400,
    "[김재중 아시아 투어MD_J-PARTY] 헤어밴드" : 400,
    "[김재중 아시아 투어MD_J-PARTY] 캐릭터 파우치" : 500,
    "[김재중 아시아 투어MD_J-PARTY] 가방" : 5000,
    "[김재중 아시아 투어MD_J-PARTY] 제이파티 키링" : 500,
    "[김재중 아시아 투어MD_J-PARTY] 김재중 목걸이" : 1000,
    "[김재중 아시아 투어MD_J-PARTY] 수면양말" : 300,
    "[김재중 아시아 투어MD_J-PARTY] 슬리퍼" : 2500,
    "[김재중 아시아 투어MD_J-PARTY] 뱃지세트" : 500,
    "[김재중 아시아 투어MD_J-PARTY] 로브" : 15000,
    "[김재중 아시아 투어MD_J-PARTY] 마스킹 테이프" : 200,
    "[김재중 아시아 투어MD_J-PARTY] 파우치" : 500,
    "[D&E(디앤이) 응원봉] D&E(디앤이) 공식 응원봉" : 3000,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 A ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 B ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 F ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 E ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 D ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 인화사진 C ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 책받침 C ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 책받침 B ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 책받침 A ver." : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 매거진" : 1000,
    "[은혁 EXPLORER 팝업스토어 MD] 스티커 세트" : 100,
    "[은혁 EXPLORER 팝업스토어 MD] 6공 다이어리" : 500,
    "[은혁 EXPLORER 팝업스토어 MD] 명찰&핀버튼 세트" : 49,
    "[은혁 EXPLORER 팝업스토어 MD] 명찰&핀버튼 세트 포토카드" : 1,
    "[은혁 EXPLORER 팝업스토어 MD] 백팩" : 4999,
    "[은혁 EXPLORER 팝업스토어 MD] 백팩 포토카드" : 1,
    "[은혁 EXPLORER 팝업스토어 MD] 헤드폰" : 1000,
    "[은혁 EXPLORER 팝업스토어 MD] 볼캡" : 999,
    "[은혁 EXPLORER 팝업스토어 MD] 볼캡 포토카드" : 1,
    "[은혁 EXPLORER 팝업스토어 MD] 트랙수트 세트" : 3750,
    "[은혁 EXPLORER 팝업스토어 MD] 아크릴 키링" : 200,
    "[BTOB 캐릭터 팝업] 20cm doll 햇냥이" : 3750,
    "[BTOB 캐릭터 팝업] 20cm doll 아토" : 3750,
    "[BTOB 캐릭터 팝업] 20cm doll 랑꼬미" : 3750,
    "[BTOB 캐릭터 팝업] 20cm doll 쁘멍" : 3750,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring 햇냥이" : 750,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring 아토" : 750,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring 랑꼬미" : 750,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring 쁘멍" : 750,
    "[BTOB 캐릭터 팝업] Scrunchie 햇냥이" : 300,
    "[BTOB 캐릭터 팝업] Scrunchie 아토" : 300,
    "[BTOB 캐릭터 팝업] Scrunchie 랑꼬미" :300,
    "[BTOB 캐릭터 팝업] Scrunchie 쁘멍" : 300,
    "[BTOB 캐릭터 팝업] Face Pouch_햇냥이" : 500,
    "[BTOB 캐릭터 팝업] Face Pouch_아토" : 500,
    "[BTOB 캐릭터 팝업] Face Pouch_랑꼬미" : 500,
    "[BTOB 캐릭터 팝업] Face Pouch_쁘멍" : 500,
    "[BTOB 캐릭터 팝업] Griptok_햇냥이" : 200,
    "[BTOB 캐릭터 팝업] Griptok_아토" : 200,
    "[BTOB 캐릭터 팝업] Griptok_랑꼬미" : 200,
    "[BTOB 캐릭터 팝업] Griptok_쁘멍" : 200,
    "[BTOB 캐릭터 팝업] Sticky Notes_햇냥이" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_아토" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_랑꼬미" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_쁘멍" : 100,
    "[BTOB 캐릭터 팝업] Sticker Set Sticker Set" : 50,
    "[BTOB 캐릭터 팝업] Card Sticker Set_햇냥이 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_햇냥이 (L)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_아토 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_아토 (L)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_랑꼬미 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_랑꼬미 (L)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_쁘멍 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_쁘멍 (L)" : 100,
    "[BTOB 캐릭터 팝업] Acrylic Shaker Keyring" : 200,
    "[BTOB 캐릭터 팝업] Room Slipper_햇냥이" : 3750,
    "[BTOB 캐릭터 팝업] Room Slipper_아토" : 3750,
    "[BTOB 캐릭터 팝업] Room Slipper_랑꼬미" : 3750,
    "[BTOB 캐릭터 팝업] Room Slipper_쁘멍" : 3750,
    "[BTOB 캐릭터 팝업] Pillow Mist Blue Orchid" : 1500,
    "[BTOB 캐릭터 팝업] Pillow Mist Morning Dew" : 1500,
    "[BTOB 캐릭터 팝업] Pillow Mist Powdery Iris" : 1500,
    "[BTOB 캐릭터 팝업] Pillow Mist Pink Musk" : 1500,
    "[BTOB 캐릭터 팝업] Bath Bomb Random Keyring Set" : 100,
    "[BTOB 캐릭터 팝업] Fabric Formula" : 3000,
    "[BTOB 캐릭터 팝업] Laundry Formula" : 3000,
    "[BTOB 캐릭터 팝업] 얼룩약 비-클린" : 2000,
    "[BTOB 캐릭터 팝업] Laundry Soap" : 1500,
    "[BTOB 캐릭터 팝업] Hand Soap" : 1500,
    "[비투비 팬콘 멜림픽 MD] IMAGE PICKET _ 프니엘" : 1000,
    "[비투비 팬콘 멜림픽 MD] IMAGE PICKET _ 임현식" : 1000,
    "[비투비 팬콘 멜림픽 MD] IMAGE PICKET _ 이민혁" : 1000,
    "[비투비 팬콘 멜림픽 MD] IMAGE PICKET _ 서은광" : 1000,
    "[비투비 팬콘 멜림픽 MD] BANDANA" : 500,
    "[비투비 팬콘 멜림픽 MD] GUIDE BOOK SET" : 1750,
    "[비투비 팬콘 멜림픽 MD] LAYERED KEYRING" : 1000,
    "[비투비 팬콘 멜림픽 MD] METAL SPORTS BOTTLE" : 1499,
    "[비투비 팬콘 멜림픽 MD] METAL SPORTS BOTTLE PHOTOCARD" : 1,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 서은광" : 500,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 이민혁" : 500,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 임현식" : 500,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 프니엘" : 500,
    "[비투비 팬콘 멜림픽 MD] POUCH CROSS BAG" : 1000,
    "[비투비 팬콘 멜림픽 MD] WIND BREAKER" : 1500,
    "[DPR Light Stick] Film" : 200,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 그립톡" : 200,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 리유저블 백" : 1000,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 마그넷" : 300,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 메모지" : 200,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 무드등" : 1500,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 스크런지" : 200,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 스티커팩" : 200,
    "[김재중 아시아투어 BEAUTY IN CHAOS MD] 실리콘 코스터" : 200,
    "[비투비 콘서트 Be Alright] 와플후드 - 카키" : 1875,
    "[프로미스나인 팝업_FROM OUR 20S] 여권 케이스" : 200,
    "[프로미스나인 팝업_FROM OUR 20S] 러기지택" : 200,
    "[프로미스나인 팝업_FROM OUR 20S] 러기지 스티커 세트" : 100,
    "[프로미스나인 팝업_FROM OUR 20S] 폴라로이드 포토카드 세트" : 100,
    "[프로미스나인 팝업_FROM OUR 20S] CD 아크릴 키링_JOURNEY ver" : 100,
    "[프로미스나인 팝업_FROM OUR 20S] 스마트톡_SYMBOL ver" : 100,
    "[프로미스나인 팝업_FROM OUR 20S] 스마트톡_TRACK ver" : 100,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring_햇냥이" : 200,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring_랑꼬미" : 200,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring_쁘멍" : 200,
    "[BTOB 캐릭터 팝업] 20cm doll_쁘멍" : 3750,
    "[BTOB 캐릭터 팝업] 20cm doll_랑꼬미" : 3750,
    "[BTOB 캐릭터 팝업] Photocard Holder_아토" : 100,
    "[BTOB 캐릭터 팝업] Scrunchie_쁘멍" : 100,
    "[BTOB 캐릭터 팝업] Laundry Soap" : 1500,
    "[BTOB 캐릭터 팝업] Hand Soap" : 1500,
    "[BTOB 캐릭터 팝업] Laundry Formula" : 3000,
    "[BTOB 캐릭터 팝업] Fabric Formula" : 3000,
    "[BTOB 캐릭터 팝업] Pillow Mist : Powdery Iris" : 1500,
    "[BTOB 캐릭터 팝업] Acrylic Shaker Keyring" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_쁘멍" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_랑꼬미" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_아토" : 100,
    "[BTOB 캐릭터 팝업] Sticky Notes_햇냥이" : 100,
    "[BTOB 캐릭터 팝업] Photocard Holder_랑꼬미" : 100,
    "[BTOB 캐릭터 팝업] Photocard Holder_햇냥이" : 100,
    "[BTOB 캐릭터 팝업] Photocard Holder_쁘멍" : 100,
    "[BTOB 캐릭터 팝업] 20cm doll_아토" : 3750,
    "[BTOB 캐릭터 팝업] 20cm doll_햇냥이" : 3750,
    "[비투비 팬콘 멜림픽 MD] POUCH CROSS BAG" : 1000,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 임현식" : 500,
    "[비투비 팬콘 멜림픽 MD] POSTCARD SET _ 서은광" : 500,
    "[BTOB 캐릭터 팝업] Scrunchie_랑꼬미" : 100,
    "[BTOB 캐릭터 팝업] Scrunchie_아토" : 100,
    "[BTOB 캐릭터 팝업] Scrunchie_햇냥이" : 100,
    "[BTOB 캐릭터 팝업] 10cm Doll keyring_아토" : 200,
    "[BTOB 캐릭터 팝업] Face Pouch_아토" : 200,
    "[BTOB 캐릭터 팝업] Pillow Mist : Morning Dew" : 1500,
    "[BTOB 캐릭터 팝업] Card Sticker Set_아토 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_랑꼬미 (S)" : 100,
    "[BTOB 캐릭터 팝업] Card Sticker Set_랑꼬미 (L)" : 100,
    "[BTOB 캐릭터 팝업] Face Pouch_랑꼬미" : 500,
    "[김재중 아시아 투어MD_J-PARTY] 아크릴 코스터" : 500,
    "[BTOB] OFFICIAL LIGHT STICK - ver.3" : 3750,
    "[DPR_Artist Merch] CREAM_psyche: red Keyring" : 300,
    "[BTOB 캐릭터 팝업] Face Pouch_쁘멍" : 500,
    "[BTOB 캐릭터 팝업] Pillow Mist : Blue Orchid" : 1500,
    "[에이티즈 콘서트 MD_IN YOUR FANTASY] 미니 파우치" : 500,
    "[에이티즈 콘서트 MD_IN YOUR FANTASY] 티셔츠 링거" : 750,
    "[에이티즈 콘서트 MD_IN YOUR FANTASY] 티셔츠 블랙" : 750,
    "[에이티즈 콘서트 MD_IN YOUR FANTASY] 풀패키지 포토카드 (8종 세트)" : 1,
    "[BTOB 캐릭터 팝업] Card Sticker Set_햇냥이 (S)" : 100,
    "[BTOB 캐릭터 팝업] Griptok_아토" : 200,
    "[이성열 팬미팅MD_YEOL'S DAY] 생일 스티커팩" : 100,
    "[이성열 팬미팅MD_YEOL'S DAY] 아크릴 키링" : 300,
    "[이성열 팬미팅MD_YEOL'S DAY] 티셔츠" : 750,
    "[이성열 팬미팅MD_YEOL'S DAY] 틴케이스 포토카드 세트" : 300,
    "[프로미스나인 콘서트MD_NOW] 트레이딩 포토카드" : 300,
    "[프로미스나인 콘서트MD_NOW] 티셔츠 - WHITE" : 750,
    "[프로미스나인] OFFICIAL LIGHT STICK Ver.2" : 1500,
    "[남우현 콘서트MD 나무고] CARABINER KEYRING" : 100,
    "[남우현 콘서트MD 나무고] CARDCOVER STICKER SET" : 50,
    "[남우현 콘서트MD 나무고] PHOTO SET" : 300,
    "[남우현 콘서트MD 나무고] PHOTOCARD POUCH SET" : 375,
    "[남우현 콘서트MD 나무고] PLUSH BADGE" : 75,
    "[남우현 콘서트MD 나무고] SCHOOL SET" : 375,
    "[남우현 콘서트MD 나무고] TRADING PHOTOCARD" : 100,
    "[이민혁 콘서트_HOOK] 랜덤 트레이딩카드" : 35,
    "[이민혁 콘서트_HOOK] 엽서북" : 75,
    "[이민혁 콘서트_HOOK] 미니카드 파우치" : 375,
    "[이민혁 콘서트_HOOK] 글러브 키링" : 75,
    "[이민혁 콘서트_HOOK] 파이핑 후드 집업" : 2500,
    "[이민혁 콘서트_HOOK] 파이핑 후드 집업 포토카드" : 30,
    "[이석훈 콘서트MD 새로 쓰임] 멀티 클리너" : 100,
    "[이석훈 콘서트MD 새로 쓰임] 종이 방향제" : 100,
    "[웬디 콘서트 MD_W:EALIVE] 반팔 티셔츠" : 750,
    "[웬디 콘서트 MD_W:EALIVE] 숄더백" : 3750,
    "[웬디 콘서트 MD_W:EALIVE] 쉬폰 패브릭 포스터" : 500,
    "[웬디 콘서트 MD_W:EALIVE] 키캡 키링" : 200,
    "[강다니엘 팬콘서트MD_RUNWAY] 러기지 스티커팩" : 200,
    "[강다니엘 팬콘서트MD_RUNWAY] 아크릴 회전 스탠드" : 500,
    "[강다니엘 팬콘서트MD_RUNWAY] 트레이딩 포토카드" : 200,
    "[강우진 팬미팅MD Blossom] 네컷포토 세트" : 200,
    "[강우진 팬미팅MD Blossom] 엽서 세트" : 500,
    "[김재중 SEASONS GREETINGS] 2026 시즌그리팅" : 1500,
    "[서은광 콘서트MD_MyPage] 랜덤 메세지 틴 캔들" : 500,
    "[서은광 콘서트MD_MyPage] 메탈 뱃지" : 200,
    "[서은광 콘서트MD_MyPage] 후드집업" : 2500,
    "[김재중_J-PARTY MD_GALAXY] 로고 키링" : 300,
    "[김재중_J-PARTY MD_GALAXY] 리유저블백" : 800,
    "[김재중_J-PARTY MD_GALAXY] 미니 키링" : 300,
    "[김재중_J-PARTY MD_GALAXY] 미니 행잉 피규어" : 500,
    "[김재중_J-PARTY MD_GALAXY] 반다나 키링" : 750,
    "[김재중_J-PARTY MD_GALAXY] 스크런치" : 500,
    "[김재중_J-PARTY MD_GALAXY] 슬로건" : 500,
    "[김재중_J-PARTY MD_GALAXY] 여권 케이스 로고버전" : 500,
    "[김재중_J-PARTY MD_GALAXY] 우산" : 1250,
    "[김재중_J-PARTY MD_GALAXY] 응원봉 배터리 캡" : 300,
    "[김재중_J-PARTY MD_GALAXY] 재랑이 인형" : 500,
    "[김재중_J-PARTY MD_GALAXY] 후드티" : 3750,
    "[서은광 콘서트MD_MyPage] 후드집업" : 3750,
    "김재중 OFFICIAL LIGHT STICK VER.2" : 3000,
    "[SF9 다원 팬미팅MD_다원해] 트레이딩 포토카드" : 30,
    "[롱샷_포토북_LNGSHOT STICKERS] 포토북" : 375,
    "[BTOB 캐릭터 팝업] Pillow Mist : Pink Musk" : 1500,
    "[김재중 SEASONS GREETINGS] 2026 시즌그리팅 데스크 캘랜더+포토카드 (1종)" : 1250,
    "[BTOB 캐릭터 팝업] Room Slipper_ 랑꼬미" : 3750,
    "[CIX GT 콘서트MD] ACRYLIC MIRROR KEYRING_SEUNGHUN ver." : 300,
    "[CIX GT 콘서트MD] ACRYLIC MIRROR KEYRING_YONGHEE ver." : 300,
    "[DPR_Artist Merch] IAN_MITO T-Shirt_Black / Size 3" : 750,
    "[SF9 다원 팬미팅MD_다원해] 키캡 키링" : 300,
    "[강다니엘 팬콘서트MD_RUNWAY] 네컷 포토 세트" : 100,
    "[강다니엘 팬콘서트MD_RUNWAY] 카드 커버 스티커" : 100,
    "[강우진 팬미팅MD Blossom] 스티커 세트" : 100,
    "[김재중 SEASONS GREETINGS] 2026 시즌그리팅 수정 스티커+포토카드 (1종)" : 100,
    "[서은광 콘서트MD_MyPage] 토트백" : 3749,
    "[서은광 콘서트MD_MyPage] 토트백 포토카드" : 1,
    "[성한빈 생일MD_Who] 미니 포토 스탠드" : 125,
    "[성한빈 생일MD_Who] 스티커 세트" : 100,
    "[성한빈 생일MD_Who] 엽서 세트" : 300,
    "[성한빈 생일MD_Who] 컬러 폴라로이드 세트" : 100,
    "[성한빈 생일MD_Who] 케이크 파우치" : 681,
    "[육성재 생일카페_YOOK] 말랑핀뱃지" : 300,
    "[육성재 생일카페_YOOK] 미니 포스터 세트" : 500,
    "[육성재 생일카페_YOOK] 밀크 글라스" : 5000,
    "[육성재 생일카페_YOOK] 키캡키링" : 300,
    "[육성재 생일카페_YOOK] 티셔츠" : 750,
    "[은혁 팬콘MD_RABBIT] 마그넷 카드 케이스 세트" : 1000,
    "[은혁 팬콘MD_RABBIT] 카라비너" : 300,
    "[은혁 팬콘MD_RABBIT] 헤어핀" : 300,
    "[은혁 팬콘MD_RABBIT] 후드집업" : 3750,
    "[이태빈 팬미팅 예약판매 MD] 아크릴 스탠드" : 300,
    "[이태빈 팬미팅 예약판매 MD] 엽서세트" : 300,
    "[이태빈 팬미팅 예약판매 MD] 패브릭 포스터" : 750,
    "[이태빈 팬미팅 예약판매 MD] 포토북" : 750
}
box_limit = 15000  # 기본 박스 최대 용량

# ───────────────────────────────────────────────────
# 제외할 재고명 목록 (처리에서 제외할 상품명을 아래에 추가)
# 예시: exclude_products = ['상품A', '상품B']
# ───────────────────────────────────────────────────
exclude_products = [
    # '상품명 예시',
]

def run_md_fs():
    st.button("◀ MD 창으로 돌아가기",
              on_click=lambda: st.session_state.update(page="md_main"),
              key="back_to_md_main_from_fs")
    st.title("📋 FS 나누기")
    uploaded = st.file_uploader("▶ FS 전용 CSV 업로드", type="csv", key="fs_csv")
    if uploaded:
        df = pd.read_csv(uploaded, dtype={'우편번호': str, '전화번호': str})

        # 제외 상품 필터링
        if exclude_products:
            before = len(df)
            df = df[~df['재고명'].astype(str).isin(exclude_products)]
            removed = before - len(df)
            if removed > 0:
                st.info(f"🗑️ 제외 상품 {removed}행 삭제됨: {exclude_products}")

        st.session_state['fs_df'] = df
        st.success(f"CSV 업로드 완료: {df.shape[0]}행")
    else:
        df = st.session_state.get('fs_df')
    missing = []
    if df is not None:
        missing = sorted(set(df['재고명'].dropna()) - set(target_products))
        if missing:
            st.warning("타겟에 정의되지 않은 재고명 발견:")
        for name in missing:
            st.code(f'"{name}" : ', language="python")
        if st.button("검증"):
            st.session_state['fs_verified'] = True
        else:
            st.success("모든 재고명이 target_products에 포함됩니다.")
            st.session_state['fs_verified'] = True
    if st.session_state.get('fs_verified') and missing:
        st.markdown("### 누락된 재고명의 무게를 입력해주세요")
        custom = st.session_state.get('fs_custom_weights', {})
        for prod in missing:
            w = st.number_input(f"{prod} ▶ 무게입력", min_value=1, key=f"w_{prod}")
            if w:
                custom[prod] = w
        st.session_state['fs_custom_weights'] = custom
    if st.session_state.get('fs_verified') and df is not None and st.button("✅ 실행"):
        merged_tp = {**target_products, **st.session_state.get('fs_custom_weights', {})}
        buf_all, buf_dom, buf_int = _process_fs(df, merged_tp, box_limit)
        st.session_state['fs_buf_all'] = buf_all.getvalue()
        st.session_state['fs_buf_dom'] = buf_dom.getvalue()
        st.session_state['fs_buf_int'] = buf_int.getvalue()
        st.success("FS 처리 완료!")
    if 'fs_buf_all' in st.session_state:
        today = datetime.datetime.now().strftime("%y%m%d")
        st.download_button("▶ 원본 시트 다운로드", st.session_state['fs_buf_all'],
                           file_name=f"FS_{today}_원본.xlsx")
        st.download_button("▶ 국내 시트 다운로드", st.session_state['fs_buf_dom'],
                           file_name=f"FS_{today}_국내.xlsx")
        st.download_button("▶ 해외 시트 다운로드", st.session_state['fs_buf_int'],
                           file_name=f"FS_{today}_해외.xlsx")
# ───────────────────────────────────────────────────
# 3) 핵심 처리 함수
# ───────────────────────────────────────────────────
def _process_fs(df: pd.DataFrame, tp: dict, limit: int):
    # [수정 추가] 안전한 연산을 위해 사전에 수량 컬럼을 정형(int) 타입으로 강제 변환합니다.
    df = df.copy()
    df['수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(0).astype(int)

    # 1) 주문 분할
    def assign_order_numbers(group):
        total_w, suffix, out = 0, 1, []
        for _, row in group.iterrows():
            weight = tp.get(row['재고명'], 0)
            qty = int(row['수량'])
            while qty > 0:
                if total_w + weight > limit:
                    suffix += 1
                    total_w = 0
                can = min(qty, (limit - total_w) // weight if weight > 0 else qty)
                nr = row.copy()
                nr['수량'] = can
                nr['주문번호'] = f"{row['주문번호']}-{suffix}"
                out.append(nr)
                total_w += can * weight
                qty -= can
        return out
    rows = []
    for _, grp in df.groupby('주문번호'):
        rows += assign_order_numbers(grp)
    res = pd.DataFrame(rows)
    # 2) 금액 처리
    res['상품금액'] = res['상품금액'].replace(0, 1)
    m = (res['국가코드'] != 'KR') & (res['결제통화'] == 'KRW')
    res.loc[m, '결제통화'] = 'USD'
    res.loc[m, '상품금액'] /= 1000
    res['실결제금액'] = res['수량'] * res['상품금액']
    res = res[res['수량'] > 0].copy()
    res['상품명'] = res['재고명']
    res.loc[res['국가명'] == "Japan", '국가명'] = "."
    dom = res[res['국가코드'] == 'KR'].copy()
    intl = res[res['국가코드'] != 'KR'].copy()
    # ⭐ [조건 반영] 해외 주문 건에 대한 국가코드별 희망배송사 자동 지정 로직 추가
    intl['희망배송사'] = intl['국가코드'].map(
        lambda c: 'sagawa' if c == 'JP' else ('emspremium' if c in ['US', 'IT', 'CO', 'RO', 'DE', 'NL', 'SE'] else 'ems')
    )
    # 3) 특전 처리
    fromis_keywords = [
        "FROM OUR 20S",
        "프로미스나인"
    ]
    def generate_bonus_rows(src):
        src = src.copy()
        src['원주문번호'] = src['주문번호'].str[:20]
        bonus = []
        mask = src['재고명'].apply(lambda x: any(k in str(x) for k in fromis_keywords))
        for oid, g in src[mask].groupby('원주num번호' if '원주num번호' in src.columns else '원주문번호'): # 오타 대응 보정
            currency = g['결제통화'].iloc[0]
            total = g['실결제금액'].sum()
            ratio = 50000 if currency == "KRW" else 50
            cnt = int(total // ratio)
            if cnt > 0:
                r = g.iloc[0].copy()
                r['주문번호'] = f"{oid}-1"
                r['재고코드'] = "301285"
                r['재고명'] = "[프로미스나인 팝업_FROM OUR 20S] MD 구매 특전 포토카드 (5종)"
                r['상품명'] = r['재고명']
                r['옵션명'] = r['재고명']
                r['수량'] = cnt
                r['상품금액'] = 1
                r['실결제금액'] = cnt
                r['결제통화'] = "USD"
                bonus.append(r)
        return pd.DataFrame(bonus, columns=src.columns)
    # dom = pd.concat([dom, generate_bonus_rows(dom)], ignore_index=True)
    # intl = pd.concat([intl, generate_bonus_rows(intl)], ignore_index=True)
    # 4) 전화번호
    def fmt(p):
        s = re.sub(r"\D", "", str(p))
        if len(s) == 11:
            return f"{s[:3]}-{s[3:7]}-{s[7:]}"
        return s
    dom['전화번호'] = dom['전화번호'].apply(fmt)
    # 5) Excel 저장
    buf_all = io.BytesIO()
    buf_dom = io.BytesIO()
    buf_int = io.BytesIO()
    with pd.ExcelWriter(buf_all, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="원본", index=False)
        dom.to_excel(w, sheet_name="국내", index=False)
        intl.to_excel(w, sheet_name="해외", index=False)
    with pd.ExcelWriter(buf_dom, engine="openpyxl") as w:
        dom.to_excel(w, sheet_name="국내", index=False)
    with pd.ExcelWriter(buf_int, engine="openpyxl") as w:
        intl.to_excel(w, sheet_name="해외", index=False)
    buf_all.seek(0)
    buf_dom.seek(0)
    buf_int.seek(0)
    return buf_all, buf_dom, buf_int
