# CHANGELOG

<!-- version list -->

## v9.2.6 (2026-05-29)

### Bug Fixes

- **manager**: Call SubscriberMixin.async_stop() from subclass teardown
  ([#388](https://github.com/Yale-Libs/yalexs/pull/388),
  [`9f0b45e`](https://github.com/Yale-Libs/yalexs/commit/9f0b45e9edcd0305be952bb6ec749e94f381fbc7))

- **socketio**: Cancel pending refresh task on disconnect and shutdown
  ([#387](https://github.com/Yale-Libs/yalexs/pull/387),
  [`9544f3f`](https://github.com/Yale-Libs/yalexs/commit/9544f3fa4f9f0f862803f71bb9bbc39d315ba5fb))


## v9.2.5 (2026-05-29)

### Bug Fixes

- **manager/subscriber**: Tolerate async_stop before any refresh scheduled
  ([#386](https://github.com/Yale-Libs/yalexs/pull/386),
  [`22bb759`](https://github.com/Yale-Libs/yalexs/commit/22bb75938331d8ce84b1c109f73f5efc88780606))

### Documentation

- **changelog**: Add PSR v10 insertion flag + backfill missed releases
  ([#383](https://github.com/Yale-Libs/yalexs/pull/383),
  [`151a396`](https://github.com/Yale-Libs/yalexs/commit/151a396b1691cf9d2354685a64d00a8ba124cc1c))

- **readme**: Refresh for async-only API + Yale Home status
  ([#379](https://github.com/Yale-Libs/yalexs/pull/379),
  [`10b4133`](https://github.com/Yale-Libs/yalexs/commit/10b4133c7f197149c60b6ff53d6874039feaa4da))

### Testing

- **activity**: Cover entity/is_status/operator-image paths (95% → 100%)
  ([#372](https://github.com/Yale-Libs/yalexs/pull/372),
  [`587f61c`](https://github.com/Yale-Libs/yalexs/commit/587f61c88cb5dd248bd64a42934869478d84c76e))

- **api_async**: Cover header preservation and retry exhaustion paths
  ([#380](https://github.com/Yale-Libs/yalexs/pull/380),
  [`c64bffd`](https://github.com/Yale-Libs/yalexs/commit/c64bffd787d1fd88f8340bd40a3a9d21c59a96af))

- **lock**: Cover setter validation and offline-key paths (93% → 100%)
  ([#370](https://github.com/Yale-Libs/yalexs/pull/370),
  [`a229541`](https://github.com/Yale-Libs/yalexs/commit/a229541a6d39bd5de3ad9c26062b31b338502949))

- **manager**: Close activity/data partial-branch gaps (99% → 100%)
  ([#378](https://github.com/Yale-Libs/yalexs/pull/378),
  [`fa27c49`](https://github.com/Yale-Libs/yalexs/commit/fa27c49fd8d22ba0e33b059655ff6a77d4bf3014))


## v9.2.4 (2026-05-29)

### Bug Fixes

- **api_async**: Pass subscriber_id to websocket get + add remove wrapper
  ([#374](https://github.com/Yale-Libs/yalexs/pull/374),
  [`bb0ce45`](https://github.com/Yale-Libs/yalexs/commit/bb0ce45c089e899a5d55111c3971335048587700))


## v9.2.3 (2026-05-28)

### Bug Fixes

- **manager/data**: Cover YaleXSData lifecycle and image paths (48% → 99%)
  ([#358](https://github.com/Yale-Libs/yalexs/pull/358),
  [`aaac78f`](https://github.com/Yale-Libs/yalexs/commit/aaac78f62dfce77237a7096ec8b9bc155f01951e))


## v9.2.2 (2026-05-28)

### Bug Fixes

- **pubnub**: Guard datetime.UTC on Py3.10 and unknown channel KeyError
  ([#353](https://github.com/Yale-Libs/yalexs/pull/353),
  [`9e7744b`](https://github.com/Yale-Libs/yalexs/commit/9e7744b6591d0de7771c0fc751e7e6477bd82d14))


## v9.2.1 (2026-05-27)

### Bug Fixes

- Drop push messages for unknown device IDs instead of raising
  ([#336](https://github.com/Yale-Libs/yalexs/pull/336),
  [`c51a8be`](https://github.com/Yale-Libs/yalexs/commit/c51a8be6c7b1d8043707b53bdef00554a28222cf))

- Replace deprecated datetime.utcfromtimestamp and datetime.utcnow
  ([#340](https://github.com/Yale-Libs/yalexs/pull/340),
  [`c18be76`](https://github.com/Yale-Libs/yalexs/commit/c18be768ad4d16312ea2cbfab538c495cf02fabc))


## v9.2.0 (2025-09-18)

### Features

- Add unified lock operation method to reduce code duplication
  ([#307](https://github.com/Yale-Libs/yalexs/pull/307),
  [`41c806d`](https://github.com/Yale-Libs/yalexs/commit/41c806d6c0e66d390f5a6da15eec0e5f2713ca6a))


## v9.1.0 (2025-09-16)

### Features

- Add support for capabilities endpoint
  ([#306](https://github.com/Yale-Libs/yalexs/pull/306),
  [`9ce477a`](https://github.com/Yale-Libs/yalexs/commit/9ce477a1a2e3a8e20da45f8bbaf108782d8f6513))


## v9.0.1 (2025-08-27)

### Bug Fixes

- Process newer status updates even when lock state unchanged
  ([#300](https://github.com/Yale-Libs/yalexs/pull/300),
  [`3f44708`](https://github.com/Yale-Libs/yalexs/commit/3f44708a4c41f59d5b9c3db37e410c8085fcd324))


## v9.0.0 (2025-08-27)

### Bug Fixes

- Drop broken Python 3.9 support
  ([#299](https://github.com/Yale-Libs/yalexs/pull/299),
  [`231eb0f`](https://github.com/Yale-Libs/yalexs/commit/231eb0f73bdf0a8a869245b54f83569a2faec7fd))

### Breaking Changes

- Drop broken Python 3.9 support. Minimum supported Python is now 3.10.


## v8.12.1 (2025-08-27)

### Bug Fixes

- Reduce excessive activity API calls and fix manual lock detection for Yale/August locks
  ([#298](https://github.com/Yale-Libs/yalexs/pull/298),
  [`eacca3d`](https://github.com/Yale-Libs/yalexs/commit/eacca3d4b352a33c7485fcb0348629a858766c90))


## v8.12.0 (2025-08-23)

### Features

- Add Yale August branding
  ([#294](https://github.com/Yale-Libs/yalexs/pull/294),
  [`7f3fcde`](https://github.com/Yale-Libs/yalexs/commit/7f3fcde909ca02876a15aa013ac32e13852b193e))


## v8.11.1 (2025-08-05)

### Bug Fixes

- Reduce excessive activity API calls for August and Yale locks
  ([#283](https://github.com/Yale-Libs/yalexs/pull/283),
  [`4f77fbd`](https://github.com/Yale-Libs/yalexs/commit/4f77fbd7dc0bd75f0f7a70bdccbcec28f6158c67))


## v8.11.0 (2025-01-20)

### Feature

* feat: adds alarm support to Yale home (#208)

Co-authored-by: pre-commit-ci[bot] &lt;66853113+pre-commit-ci[bot]@users.noreply.github.com&gt;
Co-authored-by: J. Nick Koston &lt;nick@koston.org&gt; ([`473fd0e`](https://github.com/bdraco/yalexs/commit/473fd0e0dd87a9296ff2ae48a00b2d6ce4b7d2ef))


## v8.10.0 (2024-10-06)

### Feature

* feat: add support for propcache v1.0.0+ (#192) ([`feceab8`](https://github.com/bdraco/yalexs/commit/feceab840a67a346eaecbb5eff6d3df9f8097597))


## v8.9.0 (2024-10-03)

### Feature

* feat: add support for pin lock activities (#189)

Co-authored-by: Thomas Nelson &lt;me@example.com&gt; ([`e13e977`](https://github.com/bdraco/yalexs/commit/e13e97720795e5730b309dc1e9a90c3d15204c58))


## v8.8.0 (2024-10-03)

### Feature

* feat: switch to using propcache cached_property to improve performance (#191) ([`b27dc91`](https://github.com/bdraco/yalexs/commit/b27dc9179a1ef46b33bfdc02b3d40b954a48e7aa))


## v8.7.1 (2024-09-24)

### Fix

* fix: add default first &amp; last names for pin_* actions (#188)

Co-authored-by: Thomas Nelson &lt;me@example.com&gt; ([`f2cae5b`](https://github.com/bdraco/yalexs/commit/f2cae5bc2041ee7653cc65c84823991a378365ad))


## v8.7.0 (2024-09-23)

### Feature

* feat: add support for finger unlock activities (#186)

Co-authored-by: Thomas Nelson &lt;me@example.com&gt; ([`fb5ef13`](https://github.com/bdraco/yalexs/commit/fb5ef137404121fe7761ae74950c32b584728e3d))


## v8.6.4 (2024-09-06)

### Fix

* fix: debounce activity updates to handle rapid websocket updates (#182) ([`bf3b0a1`](https://github.com/bdraco/yalexs/commit/bf3b0a141f130dc5c32d590b1fbdcf28250cc887))


## v8.6.3 (2024-09-03)

### Fix

* fix: battery state not refreshing (#181) ([`78cf869`](https://github.com/bdraco/yalexs/commit/78cf869c5d0a184e0f58aa5ba7ba76adda99116b))


## v8.6.2 (2024-09-03)

### Fix

* fix: remove yale global pubnub tokens (#180) ([`f715ae1`](https://github.com/bdraco/yalexs/commit/f715ae1d8abb878f5707017b6da66f4f91423f89))


## v8.6.1 (2024-09-03)

### Fix

* fix: restore doorbell support for yale global brand (#179) ([`219d176`](https://github.com/bdraco/yalexs/commit/219d176b5f8e9c0f414f19e49a08f1f679c7b2a7))


## v8.6.0 (2024-09-02)

### Feature

* feat: add support for linked lock activities (#177) ([`5eed87b`](https://github.com/bdraco/yalexs/commit/5eed87bda1f6fa0f1f422105a265f8d8af884b83))


## v8.5.5 (2024-08-29)

### Fix

* fix: improve handling of 502 errors (#174) ([`e19264b`](https://github.com/bdraco/yalexs/commit/e19264bd5aa7e8e51fdde1337c38c917918f7f96))


## v8.5.4 (2024-08-27)

### Fix

* fix: bump socketio to 5+ (#173) ([`ab5a6c8`](https://github.com/bdraco/yalexs/commit/ab5a6c842b413a134e52558c10570cdcdc8c0079))


## v8.5.3 (2024-08-27)

### Fix

* fix: doorbell image retry with yale global brand (#172) ([`4a41de5`](https://github.com/bdraco/yalexs/commit/4a41de5b09fd1381d9c1e76140d5138f859f15b1))


## v8.5.2 (2024-08-27)

### Fix

* fix: disable excessive logging (#171) ([`7e01490`](https://github.com/bdraco/yalexs/commit/7e014908f28f0a0d642bd923029400f402927f85))


## v8.5.1 (2024-08-27)

### Fix

* fix: lower socketio to 4 for ha compat (#170) ([`1ae7c88`](https://github.com/bdraco/yalexs/commit/1ae7c88b97d64a9ab88ea74911ea044c1b74c1a0))


## v8.5.0 (2024-08-27)

### Feature

* feat: add socketio support for websockets (#165) ([`f260c82`](https://github.com/bdraco/yalexs/commit/f260c82d9c7c396fcca584ebfa51e5f808a802c3))


## v8.4.2 (2024-08-25)

### Fix

* fix: removing polling fallback (#168) ([`f346fa3`](https://github.com/bdraco/yalexs/commit/f346fa30f777426b9b507985f0dc75ad7d0325ff))


## v8.4.1 (2024-08-25)

### Fix

* fix: ensure init sync does not check rate limit (#166) ([`9548850`](https://github.com/bdraco/yalexs/commit/9548850eb09f7c79d7ad2619b0181ff5c079bc93))


## v8.4.0 (2024-08-24)

### Feature

* feat: add constant for brands without oauth required (#164) ([`7c472c0`](https://github.com/bdraco/yalexs/commit/7c472c02beba7d4ba998c0ff9ae3e191b8b96b2d))


## v8.3.3 (2024-08-23)

### Fix

* fix: shutdown faster by doing pubnub shutdown last (#162)

* fix: shutdown faster by doing pubnub shutdown last

* more guards

* fix: move rate limit check sooner to avoid getting blocked

* fix: move rate limit check sooner to avoid getting blocked

* fix: ensure rate limit kicks in on failure as well

* fix: register point ([`735ba94`](https://github.com/bdraco/yalexs/commit/735ba9421ea211c43bb72fc7043e2e408108f949))


## v8.3.2 (2024-08-23)

### Fix

* fix: check for oauth required in async_authenticate to avoid auth being cleared (#161) ([`a849351`](https://github.com/bdraco/yalexs/commit/a849351d130c1781544c50236115f386252b20e1))


## v8.3.1 (2024-08-23)

### Fix

* fix: always send brand header (#160) ([`c0b1fad`](https://github.com/bdraco/yalexs/commit/c0b1fadde651d24ada25f54ef8d0c70ff04bc992))


## v8.3.0 (2024-08-23)

### Feature

* feat: add require oauth flag (#159) ([`a336e47`](https://github.com/bdraco/yalexs/commit/a336e47abee337700ba4f851fb1e70be75d8c263))


## v8.2.0 (2024-08-23)

### Feature

* feat: implement rate limit checker to avoid getting blocked (#158) ([`7dfb92b`](https://github.com/bdraco/yalexs/commit/7dfb92b93b591e8e54c7158048c1ccbdd4a3a3ad))


## v8.1.4 (2024-08-22)

### Fix

* fix: add missing commitlint config (#157) ([`26d7a4a`](https://github.com/bdraco/yalexs/commit/26d7a4a0f011ca8e5ca2c18d1c6ec2876bccd0da))


## v8.1.3 (2024-08-22)

### Fix

* fix: timestamp division for datetime generation in tests (#156) ([`446d3ec`](https://github.com/bdraco/yalexs/commit/446d3eceb74f9838b55299d310a39d6ee061cadc))


## v8.1.2 (2024-08-20)

### Fix

* fix: ensure subclassed AugustApiAIOHTTPError is back-compat (#155) ([`8304c3b`](https://github.com/bdraco/yalexs/commit/8304c3bca9ab6260662c87e1b51698b48bef9bf5))


## v8.1.1 (2024-08-20)

### Fix

* fix: handle 429 error was yale error (#154) ([`e450a76`](https://github.com/bdraco/yalexs/commit/e450a7667250d3c4b69bd5459628fa45346b15e2))


## v8.1.0 (2024-08-20)

### Feature

* feat: cleanup exceptions to avoid duplication (#153) ([`51af44e`](https://github.com/bdraco/yalexs/commit/51af44e64abb0a804179cef12b1dda903cbff7c5))


## v8.0.2 (2024-08-13)

### Fix

* fix: library version pins being too narrow (#149) ([`9cd8b13`](https://github.com/bdraco/yalexs/commit/9cd8b13475b50662f81885f9a7948d2f782a2616))


## v8.0.1 (2024-08-13)

### Fix

* fix: doorbells are not supported with yale global brand (#148) ([`a85ca5c`](https://github.com/bdraco/yalexs/commit/a85ca5ccf33fc082452ab2b790912aaa61bdbd0c))


## v8.0.0 (2024-08-13)

### Breaking

* feat!: add yale global support (#146) ([`5dc4bd7`](https://github.com/bdraco/yalexs/commit/5dc4bd7c41561e09a5e34440a163ae5d4b27a3af))

### Fix

* fix: force release (#147) ([`b409c80`](https://github.com/bdraco/yalexs/commit/b409c80eaefc854938449d66419ae49f843efd73))


## v7.1.3 (2024-08-13)

### Fix

* fix: temp use yale home keys for key global (#145) ([`a22beb8`](https://github.com/bdraco/yalexs/commit/a22beb869e239ba53ed62e622b76056db4c712d6))


## v7.1.2 (2024-08-13)

### Fix

* fix: handle empty login method for oauth (#144) ([`b686ceb`](https://github.com/bdraco/yalexs/commit/b686ceba5fde4247c32803730fe17106125e6544))


## v7.1.1 (2024-08-13)

### Fix

* fix: handle oauth when there is no username saved (#143) ([`317f674`](https://github.com/bdraco/yalexs/commit/317f6747a0a09129de9c44ae8e2872ea060571c9))


## v7.1.0 (2024-08-13)

### Feature

* feat: allow passing an auth class (#142) ([`377d75c`](https://github.com/bdraco/yalexs/commit/377d75cb4cb2cee6d0294fbf3acebb1b3c39798c))


## v7.0.0 (2024-08-13)

### Breaking

* feat!: remove sync api (#141) ([`6a0db94`](https://github.com/bdraco/yalexs/commit/6a0db9426e4ba586a3449ff2a7d549f0035a1255))

### Feature

* feat: add yale global brand (#140) ([`597e9f9`](https://github.com/bdraco/yalexs/commit/597e9f9bc6693093dc1bdeb2c56b41ba22d161ca))


## v6.6.0 (2024-08-13)

### Feature

* feat: make fetching the access token a coro (#139) ([`451080d`](https://github.com/bdraco/yalexs/commit/451080d50f261566cb8a4feeeac6a92e5b76634d))


## v6.5.1 (2024-08-13)

### Fix

* fix: cleanup _async_dict_to_api for oauth conversion (#138) ([`a41474d`](https://github.com/bdraco/yalexs/commit/a41474d98bc1f56fe014f9a1ac09c32aed7afc14))


## v6.5.0 (2024-08-12)

### Feature

* feat: cleanup activity construction code (#136) ([`b994c0b`](https://github.com/bdraco/yalexs/commit/b994c0be4f3500abc954a718a77c78fa332498f2))


## v6.4.4 (2024-08-05)

### Fix

* fix: tests with aiohttp &gt;= 3.10.0 (#134) ([`a25deb4`](https://github.com/bdraco/yalexs/commit/a25deb453a19854cd5f5c7eb1cc3114718248880))


## v6.4.3 (2024-07-15)

### Fix

* fix: replace pubnub with freenub to keep MIT license (#130) ([`57e41af`](https://github.com/bdraco/yalexs/commit/57e41af16331d2031294107cd1f438fab3e3a524))


## v6.4.2 (2024-07-07)

### Fix

* fix: keypad battery level for non-english locales (#128) ([`cca641f`](https://github.com/bdraco/yalexs/commit/cca641ff829984f7144be7fccf29ca50816aa38b))


## v6.4.1 (2024-06-23)

### Fix

* fix: blocking I/O in the event loop to stat the auth file (#123) ([`44ce0c4`](https://github.com/bdraco/yalexs/commit/44ce0c44c12c7c18ec12d83261346fdc25917afe))


## v6.4.0 (2024-06-19)

### Feature

* feat: abstract sources to tell which ones are push (#122) ([`7b0fdb9`](https://github.com/bdraco/yalexs/commit/7b0fdb90d4d67423c8e51fabc3098243e7805e8d))


## v6.3.0 (2024-06-18)

### Feature

* feat: expose the brand on the data object for backwards compat (#121) ([`1e04f18`](https://github.com/bdraco/yalexs/commit/1e04f18c6c9479f680302f2afa2c352454ba2efc))


## v6.2.0 (2024-06-18)

### Feature

* feat: add async_get_doorbell_image method to the YaleXSData object (#120) ([`a33b842`](https://github.com/bdraco/yalexs/commit/a33b84237721f28a43c95dce81ec6400868a9e15))


## v6.1.1 (2024-06-18)

### Fix

* fix: handle teardown if setup is cancelled (#119) ([`cb50051`](https://github.com/bdraco/yalexs/commit/cb500517d3cb3a6a413fdd8515f3de21a6a0523b))


## v6.1.0 (2024-06-18)

### Feature

* feat: abstract the need to check pubnub since it yale will use websocets (#118) ([`4aabe59`](https://github.com/bdraco/yalexs/commit/4aabe59cb19b9dcece2297900d325dca4e837175))


## v6.0.0 (2024-06-10)

### Breaking

* feat!: Add data module (#116) ([`14d6513`](https://github.com/bdraco/yalexs/commit/14d65137a3967d0a9f10264b49dc591f643d9f3a))

### Fix

* fix: bump commitlint to v6 (#117) ([`af95d48`](https://github.com/bdraco/yalexs/commit/af95d48665bb3e3c44a2b60b95600473a546b4df))


## v5.2.0 (2024-06-09)

### Feature

* feat: improve performance of subscribers (#115) ([`98bb11a`](https://github.com/bdraco/yalexs/commit/98bb11a5eedd2188cca73d39e21101a57c6e3415))


## v5.1.2 (2024-06-09)

### Fix

* fix: allow pubnub unsub to complete since nothing currently waits (#114) ([`82b0c58`](https://github.com/bdraco/yalexs/commit/82b0c58a0ed64afa107145be2ad161039e6a8a3a))


## v5.1.1 (2024-06-09)

### Fix

* fix: cleanup duplicate code in pubnub (#113) ([`6c189e2`](https://github.com/bdraco/yalexs/commit/6c189e22af847a2760522d3f75c9ef7250cbeadc))


## v5.1.0 (2024-06-09)

### Feature

* feat: cleanup pubnub code (#112) ([`67fc84a`](https://github.com/bdraco/yalexs/commit/67fc84a838bf584ce57e10a9294d066c4c0b67a6))


## v5.0.1 (2024-06-09)

### Fix

* fix: typing on async_create_pubnub (#111) ([`c02b3e8`](https://github.com/bdraco/yalexs/commit/c02b3e82dcb9ec540a090bbb90cdf9b0ac0b26be))


## v5.0.0 (2024-06-09)

### Breaking

* fix!: async_create_pubnub now returns a coro that needs to be awaited… (#110) ([`e1de91a`](https://github.com/bdraco/yalexs/commit/e1de91a428280808e20db6582472cd0e2fe938ba))


## v4.0.0 (2024-06-08)

### Breaking

* feat!: add manager (#109) ([`107a747`](https://github.com/bdraco/yalexs/commit/107a747d040c3a233845adaee1e8cbc0c27f05d0))


## v3.2.0 (2024-06-08)

### Feature

* feat: switch to poetry (#108) ([`e7d4609`](https://github.com/bdraco/yalexs/commit/e7d460944c803be814b539fa4d439d12090d0b74))


## v3.1.0 (2024-05-01)

### Unknown

* Bump version: 3.0.1 → 3.1.0 ([`74ab415`](https://github.com/bdraco/yalexs/commit/74ab415bf73c0ba6e65b87e1d154fda32a78fa9b))

* async_unlatch_return_activities tests and fixtures (#103)

Co-authored-by: J. Nick Koston &lt;nick@koston.org&gt; ([`b0b4d94`](https://github.com/bdraco/yalexs/commit/b0b4d9479bcfd0a87a46ce3ebe9665caf9b09b54))

* fix codecov by adding token (#106) ([`79070f7`](https://github.com/bdraco/yalexs/commit/79070f7340a60dfe6c7391e099f71902e9459fdb))

* add unlatch property to lock (#105) ([`28b4263`](https://github.com/bdraco/yalexs/commit/28b42632eb2c8ef06a577990abc3bdb55d4b6193))


## v3.0.1 (2024-04-03)

### Unknown

* Bump version: 3.0.0 → 3.0.1 ([`5897263`](https://github.com/bdraco/yalexs/commit/58972630c697fd5f64450a2044590391d9da2eb0))

* Improve performance of activity processing (#104) ([`3089b70`](https://github.com/bdraco/yalexs/commit/3089b708b4b84c06fb9d2ca0dde610eafe4c5c21))


## v3.0.0 (2024-03-19)

### Unknown

* Bump version: 2.0.0 → 3.0.0 ([`3dc3750`](https://github.com/bdraco/yalexs/commit/3dc3750af51952783b8d604d681254c28657a825))

* Add unlatch action (#101) ([`26d1305`](https://github.com/bdraco/yalexs/commit/26d130510bcc88d3618e1b3f552744108952aa7c))


## v2.0.0 (2024-02-28)

### Unknown

* Bump version: 1.11.4 → 2.0.0 ([`2fb5f85`](https://github.com/bdraco/yalexs/commit/2fb5f85df8dcaafd8f5f819bfcde8bd91d639a44))

* Camera content-token raise error on expiry (#97) ([`0719fb5`](https://github.com/bdraco/yalexs/commit/0719fb56e3c599f1783357e6497077d90e99db51))


## v1.11.4 (2024-02-27)

### Unknown

* Bump version: 1.11.3 → 1.11.4 ([`7bc4617`](https://github.com/bdraco/yalexs/commit/7bc4617288cbf753ee3ef9a04b44070431ffaf4a))

* Bump pubnub to 7.4.1 (#98) ([`c4ffd9a`](https://github.com/bdraco/yalexs/commit/c4ffd9a202ab0570f7d55a91ff95d6eea364b32b))


## v1.11.3 (2024-02-26)

### Unknown

* Bump version: 1.11.2 → 1.11.3 ([`6ff849e`](https://github.com/bdraco/yalexs/commit/6ff849ead7849169aacdf76feb1ee8b24ea7bb37))

* Don&#39;t create activity from lock status polls (#95) ([`289da40`](https://github.com/bdraco/yalexs/commit/289da4019cd5393dab2c8e0c33bb9621a43a64db))


## v1.11.2 (2024-02-10)

### Unknown

* Bump version: 1.11.1 → 1.11.2 ([`9a68e17`](https://github.com/bdraco/yalexs/commit/9a68e17ac4292a914520759d88169a9a85668caa))

* Add missing actions for home key (#94) ([`83e6df7`](https://github.com/bdraco/yalexs/commit/83e6df7d0d3401dd0483c9bc075550ba88e19e95))


## v1.11.1 (2024-02-09)

### Unknown

* Bump version: 1.11.0 → 1.11.1 ([`2dd2f23`](https://github.com/bdraco/yalexs/commit/2dd2f23505a3ba2bad1d9cdd6626b193f1469803))

* Add contentToken Auth header for camera images (Yale home) (#92)

Co-authored-by: Alexander Björck &lt;alexander.bjorck@assaabloy.com&gt;
Co-authored-by: J. Nick Koston &lt;nick@koston.org&gt; ([`b41e8cb`](https://github.com/bdraco/yalexs/commit/b41e8cbf250b29d45e3b962e1c69d3cb3a39259b))


## v1.11.0 (2024-01-24)

### Unknown

* Bump version: 1.10.0 → 1.11.0 ([`3474eb0`](https://github.com/bdraco/yalexs/commit/3474eb00fe3fb7fa3855b3e3df58b51e2d9004de))

* Add ssl context helper (#90) ([`a004dd9`](https://github.com/bdraco/yalexs/commit/a004dd99ad9e73c09c25311df298bf702df07db7))


## v1.10.0 (2023-09-21)

### Unknown

* Bump version: 1.9.0 → 1.10.0 ([`c75cb85`](https://github.com/bdraco/yalexs/commit/c75cb850d391758f8cf46c538d65b3344517659f))

* Add more activity types (#87) ([`983fc58`](https://github.com/bdraco/yalexs/commit/983fc580c7e78c6903ee0d8976b9d22159e4d349))


## v1.9.0 (2023-09-13)

### Unknown

* Bump version: 1.8.1 → 1.9.0 ([`4ea45b2`](https://github.com/bdraco/yalexs/commit/4ea45b2fc6af504f0a086c1e9a889eb2f30c56d3))


## v1.8.1 (2023-09-13)

### Unknown

* Bump version: 1.8.0 → 1.8.1 ([`58692fe`](https://github.com/bdraco/yalexs/commit/58692fe5760c0f27e0b7d08025e5c6a30deda05a))

* Add support for type 10 doormans (#85) ([`1a5b242`](https://github.com/bdraco/yalexs/commit/1a5b242fc00a8fd7d749c3284a2e97a171f5408e))


## v1.8.0 (2023-08-21)

### Unknown

* Bump version: 1.7.0 → 1.8.0 ([`f473535`](https://github.com/bdraco/yalexs/commit/f473535b6f033078045ee1ac82a153530ed972ee))

* Cache timestamp conversion (#84) ([`8fc664d`](https://github.com/bdraco/yalexs/commit/8fc664d70a7d8c26e6161503f43581588066c7b8))


## v1.7.0 (2023-08-21)

### Unknown

* Bump version: 1.6.0 → 1.7.0 ([`9572fe1`](https://github.com/bdraco/yalexs/commit/9572fe175afc2809fe496748840d30704fa2b2af))

* Speed up activity processing (#83) ([`4c4a06e`](https://github.com/bdraco/yalexs/commit/4c4a06e72b1ce15ef6a5f4cedfcbb4b7c1034576))


## v1.6.0 (2023-08-21)

### Unknown

* Bump version: 1.5.2 → 1.6.0 ([`531dd24`](https://github.com/bdraco/yalexs/commit/531dd24e116befadaf554c21c4bbb6035dd570a2))

* Defer construction of activities and use property caching (#82) ([`d95f1d7`](https://github.com/bdraco/yalexs/commit/d95f1d71c77878ee0fc53ffd8067f8176f8355e5))


## v1.5.2 (2023-08-07)

### Feature

* feat: add support for detecting locks that have a doorbell (#81) ([`54eec8e`](https://github.com/bdraco/yalexs/commit/54eec8ee6db112f4573f0ba965cb0953b2497e6a))

### Unknown

* Bump version: 1.5.1 → 1.5.2 ([`47d1500`](https://github.com/bdraco/yalexs/commit/47d150082988e821aa67734423d226b24745f00d))


## v1.5.1 (2023-05-22)

### Unknown

* Bump version: 1.5.0 → 1.5.1 ([`e836026`](https://github.com/bdraco/yalexs/commit/e836026d639764e92b6cc9294dee6d4d2a6b3cc3))

* Fix missing await in api retry (#75) ([`45d1de3`](https://github.com/bdraco/yalexs/commit/45d1de38b586992fb0dee7bcecd7f5e157708943))


## v1.5.0 (2023-05-22)

### Unknown

* Bump version: 1.4.6 → 1.5.0 ([`7bff08c`](https://github.com/bdraco/yalexs/commit/7bff08cee84ed099b4f59c58b7f97a86fd33f8d3))

* Speed up parsing datetimes (#74) ([`9c92c0c`](https://github.com/bdraco/yalexs/commit/9c92c0c0e47e3a0fb3ec9a5f55f3f723b5d48d27))

* Add support for fetching the configuration URL (#73) ([`8ba22b9`](https://github.com/bdraco/yalexs/commit/8ba22b986f6485d8a5c820be00f1ac3890db2a4a))

* Fix typing on async_create_pubnub (#72) ([`06ccffb`](https://github.com/bdraco/yalexs/commit/06ccffb5b7e84ffdc8acfb073202a257ce7f53cd))

* Add test for manuallock (#71) ([`94d28d3`](https://github.com/bdraco/yalexs/commit/94d28d399371f4defa591b093cfe3cd644d86a91))

* Add test for manualunlock (#70) ([`21aac10`](https://github.com/bdraco/yalexs/commit/21aac1040c58777593ad8ab512fd52855c06e560))

* Use relative imports (#69) ([`7165e78`](https://github.com/bdraco/yalexs/commit/7165e7879f407aa170ea1b5ea08c0d090c503eb9))


## v1.4.6 (2023-05-18)

### Unknown

* Bump version: 1.4.5 → 1.4.6 ([`61f88a2`](https://github.com/bdraco/yalexs/commit/61f88a236f0d8cb0906af0a068f4c02d26bcbb0e))

* Add more retries (#68) ([`5fa20a8`](https://github.com/bdraco/yalexs/commit/5fa20a8a9b91a4176a5e8b7f8555e43e3e9063b9))

* Handle more cases of bridge offline (#67) ([`46805b8`](https://github.com/bdraco/yalexs/commit/46805b8b5ea599faddc3d5768841c49d63892b4c))


## v1.4.5 (2023-05-18)

### Unknown

* Bump version: 1.4.4 → 1.4.5 ([`87bc81c`](https://github.com/bdraco/yalexs/commit/87bc81c384df69c0b3678b5d3f6cfece5d2f8f2a))

* Update tokens for Yale Home (#66) ([`5466b3c`](https://github.com/bdraco/yalexs/commit/5466b3c33678b837ac046efa70cf43dea10d0eb9))


## v1.4.4 (2023-05-17)

### Unknown

* Bump version: 1.4.3 → 1.4.4 ([`105045d`](https://github.com/bdraco/yalexs/commit/105045d4cc05e2f80588809bfd728a4207ebb135))

* Adjust brand header based on brand (#65) ([`aaba169`](https://github.com/bdraco/yalexs/commit/aaba1692051ed28177fb35d44d04f0450812fb26))


## v1.4.3 (2023-05-17)

### Unknown

* Bump version: 1.4.2 → 1.4.3 ([`7678a09`](https://github.com/bdraco/yalexs/commit/7678a09337018a3e794d896eb3cbc244b41a3a0c))

* Fix handling wrong code and hide password in logging (#64) ([`d3a6010`](https://github.com/bdraco/yalexs/commit/d3a6010db33d1e022df71647525cff0b99256b95))


## v1.4.2 (2023-05-17)

### Unknown

* Bump version: 1.4.1 → 1.4.2 ([`cf048d8`](https://github.com/bdraco/yalexs/commit/cf048d876c567721e78cd729df8ff1b1da132b88))

* Fix some typing (#63) ([`3fddde8`](https://github.com/bdraco/yalexs/commit/3fddde8887118820493c14e108e02c574125e58b))


## v1.4.1 (2023-05-17)

### Unknown

* Bump version: 1.4.0 → 1.4.1 ([`530791d`](https://github.com/bdraco/yalexs/commit/530791dc9efea965c872937c8e1efb61aceb42ee))

* Handle late auth failure when switching brands (Yale Home) (#62) ([`5a960fa`](https://github.com/bdraco/yalexs/commit/5a960fa12efde95a357f27d280828f3e6561b2b8))


## v1.4.0 (2023-05-17)

### Unknown

* Bump version: 1.3.3 → 1.4.0 ([`072901e`](https://github.com/bdraco/yalexs/commit/072901ed8225504bc794358e0dd64b0b3d98353a))

* Preliminary support for Yale Home (#61) ([`c73b38c`](https://github.com/bdraco/yalexs/commit/c73b38c0d29e13f8e766309125a66ec90db8e514))


## v1.3.3 (2023-04-30)

### Fix

* fix: handle activities that happen at the same microsecond (#57) ([`4dca5db`](https://github.com/bdraco/yalexs/commit/4dca5dbe8e050852a223e20fac74f8b763ebc1e7))

### Unknown

* Bump version: 1.3.2 → 1.3.3 ([`c7c7c43`](https://github.com/bdraco/yalexs/commit/c7c7c4381ba1799440346192d01f1ffc7f4883ae))


## v1.3.2 (2023-04-24)

### Unknown

* Bump version: 1.3.1 → 1.3.2 ([`fc43ee7`](https://github.com/bdraco/yalexs/commit/fc43ee770a47cfff6a8505023fb55d1d566dfd7d))

* Avoid setting the operator if the lock event is a replay (#56) ([`47a9d04`](https://github.com/bdraco/yalexs/commit/47a9d04a2097b5ad16bf163f758be942b890c38f))


## v1.3.1 (2023-04-24)

### Unknown

* Bump version: 1.3.0 → 1.3.1 ([`493f702`](https://github.com/bdraco/yalexs/commit/493f702c5ed46f7d9ef263f0b2d8b1e00198c2f3))

* Fix incorrect times from pubnub messages (#55) ([`fab0619`](https://github.com/bdraco/yalexs/commit/fab06194ebde1ba0cc07e2eb7d2f2ec248d4c055))

* Add support for doorman l3 doorbell event (#54)

Co-authored-by: J. Nick Koston &lt;nick@koston.org&gt; ([`637fdd6`](https://github.com/bdraco/yalexs/commit/637fdd6962b009255b92483ec3ec31958d7168e8))


## v1.3.0 (2023-04-15)

### Unknown

* Bump version: 1.2.9 → 1.3.0 ([`0f0954a`](https://github.com/bdraco/yalexs/commit/0f0954a8dbc9ff174d1cda4a585819d37e960c99))


## v1.2.9 (2023-04-15)

### Unknown

* Bump version: 1.2.8 → 1.2.9 ([`0f23d20`](https://github.com/bdraco/yalexs/commit/0f23d209530d709ee0ceb4cd0a7a5d0de0397e00))

* Handle alternate user ID field in events (#53)

Co-authored-by: J. Nick Koston &lt;nick@koston.org&gt; ([`f8a3afa`](https://github.com/bdraco/yalexs/commit/f8a3afaa1367252ba363af492475b09249f5e23f))


## v1.2.8 (2023-02-20)

### Unknown

* Bump version: 1.2.7 → 1.2.8 ([`0af3db1`](https://github.com/bdraco/yalexs/commit/0af3db15b187075f6847602c2978e58d1297340d))

* Key error when there are accessType &#34;always&#34; (#48) ([`25e69d8`](https://github.com/bdraco/yalexs/commit/25e69d8ac76515857bd40a2fd87f9ed0dd49394f))


## v1.2.7 (2023-02-17)

### Unknown

* Bump version: 1.2.6 → 1.2.7 ([`a68f8d4`](https://github.com/bdraco/yalexs/commit/a68f8d45a7b09a14cf894e7c7524b86aa2bb0878))

* Fix missing microseconds in time conversion (#47) ([`888cf9c`](https://github.com/bdraco/yalexs/commit/888cf9c82a9cd26fb2e024fba4edf9d1567e604b))


## v1.2.6 (2022-10-12)

### Unknown

* Bump version: 1.2.5 → 1.2.6 ([`9536fed`](https://github.com/bdraco/yalexs/commit/9536fed0965941ceeff04c78ef9f42f3db66ea63))

* Add names to local lock operations for compat (#43) ([`26e7b06`](https://github.com/bdraco/yalexs/commit/26e7b06ab786d6922951e9fc0bcae3ff4088e382))

* add more activity tests (#42) ([`4980073`](https://github.com/bdraco/yalexs/commit/4980073d91322b0228fb9dcae0b9c92285ea04d8))

* add tests for manual operations (#41) ([`71fea19`](https://github.com/bdraco/yalexs/commit/71fea1970f5beda1c90c5c181eb62f8f4e4e5280))


## v1.2.5 (2022-10-12)

### Unknown

* Bump version: 1.2.4 → 1.2.5 ([`def745a`](https://github.com/bdraco/yalexs/commit/def745a8789f89eef6535516f38c142793255809))

* Add support for additional activities (#40) ([`d4b1569`](https://github.com/bdraco/yalexs/commit/d4b156991cf901c8bb65a7b9f917ca10d4f167da))


## v1.2.4 (2022-09-29)

### Fix

* fix: doorbell parser for new api (#38) ([`c757289`](https://github.com/bdraco/yalexs/commit/c757289097de93cdf69385a2022ad7c1e7251757))

### Unknown

* Bump version: 1.2.3 → 1.2.4 ([`2996d8a`](https://github.com/bdraco/yalexs/commit/2996d8a143e282b8689137505631a409a66acdc9))


## v1.2.3 (2022-09-28)

### Feature

* feat: map additional activities (#37) ([`1868282`](https://github.com/bdraco/yalexs/commit/18682827d358a3f38bbbe9cc2e74b449c46c8f84))

### Unknown

* Bump version: 1.2.2 → 1.2.3 ([`d4df7ec`](https://github.com/bdraco/yalexs/commit/d4df7ecb6a38b9418338544cf88fd6b3b25cb4ae))


## v1.2.2 (2022-09-23)

### Unknown

* Bump version: 1.2.1 → 1.2.2 ([`e9f496a`](https://github.com/bdraco/yalexs/commit/e9f496a86cddf5fe33e0d43580757fb1c81a4f82))

* Update for activity api change (#36) ([`8ba4e65`](https://github.com/bdraco/yalexs/commit/8ba4e65da7513a525187d76b7a3eafaa477aef13))


## v1.2.1 (2022-08-06)

### Unknown

* Bump version: 1.2.0 → 1.2.1 ([`6c82e9b`](https://github.com/bdraco/yalexs/commit/6c82e9b4a51023c87923071dcde128b776804f7a))

* Expose mac address on api (#32) ([`7dc0b88`](https://github.com/bdraco/yalexs/commit/7dc0b88a73b3251d9bd565fd2a0c0713654f3a71))


## v1.2.0 (2022-07-28)

### Unknown

* Bump version: 1.1.25 → 1.2.0 ([`cc2377a`](https://github.com/bdraco/yalexs/commit/cc2377a6dcc5ec106a8a61789347918250add625))

* Add support for getting the offline keys (#31) ([`4ff8d98`](https://github.com/bdraco/yalexs/commit/4ff8d98d2ca213ac1258e529c71f519d6b04fd37))


## v1.1.25 (2022-05-11)

### Unknown

* Bump version: 1.1.24 → 1.1.25 ([`01a2964`](https://github.com/bdraco/yalexs/commit/01a2964e789abeae71a51ba7f9f995565389a996))

* Handling secure mode (#29)

When setting the lock in &#34;secure mode&#34; (cannot be physically opened from the inside) august reports `kAugLockState_SecureMode`. This isn&#39;t interpenetrated as locked.

This change proposes to change that. ([`0480734`](https://github.com/bdraco/yalexs/commit/048073440bb2f1852abbcc2da077c9833a0a13e9))


## v1.1.24 (2022-05-06)

### Unknown

* Bump version: 1.1.23 → 1.1.24 ([`0291b0a`](https://github.com/bdraco/yalexs/commit/0291b0a650f78fc307ddf6ced74abab8715b41ba))

* Only parse Authentication expire time once (#28) ([`6abae88`](https://github.com/bdraco/yalexs/commit/6abae883220f53f5bf9d6b3fa603362d77944c55))


## v1.1.23 (2022-03-15)

### Unknown

* Bump version: 1.1.22 → 1.1.23 ([`95d4b80`](https://github.com/bdraco/yalexs/commit/95d4b80bbd989ca01a9b41b22d1860d91b0d405a))

* Provide raw access to data for diagnostics (#27) ([`9e43427`](https://github.com/bdraco/yalexs/commit/9e43427adf068c9158e43c77ff34fa4e8f779a0d))


## v1.1.22 (2022-02-11)

### Unknown

* Bump version: 1.1.21 → 1.1.22 ([`98cc55c`](https://github.com/bdraco/yalexs/commit/98cc55c0ce8dd5915c8e0257e0cd55ba715c6247))

* Switch to using JWT for token decoding to handle emojii (#26) ([`8000542`](https://github.com/bdraco/yalexs/commit/80005429ba49c1029e96cf74a13d1d4d355eb142))


## v1.1.21 (2022-02-11)

### Unknown

* Bump version: 1.1.20 → 1.1.21 ([`b3dd252`](https://github.com/bdraco/yalexs/commit/b3dd2520fb5407b7ae985c918d431a90dff41010))

* Add additional debug logging (#25) ([`2fee78d`](https://github.com/bdraco/yalexs/commit/2fee78df329891c4b2354bfc04c710be05e84b71))


## v1.1.20 (2022-01-31)

### Unknown

* Bump version: 1.1.19 → 1.1.20 ([`fa2a139`](https://github.com/bdraco/yalexs/commit/fa2a139eeeff98a9f15c19e4acbb18151d15e146))

* Update august agent (#24) ([`88abc08`](https://github.com/bdraco/yalexs/commit/88abc08684f9536962ba19289b1b841c0b684bb0))


## v1.1.19 (2022-01-15)

### Unknown

* Bump version: 1.1.18 → 1.1.19 ([`35d38ac`](https://github.com/bdraco/yalexs/commit/35d38ac820db362d0a0155b19f430ac650948418))

* Fix unlock/lock with older bridges (#23) ([`b620936`](https://github.com/bdraco/yalexs/commit/b6209366b0387073db7d16301d592ddfd4b06f0d))


## v1.1.18 (2022-01-13)

### Unknown

* Bump version: 1.1.17 → 1.1.18 ([`88dbab7`](https://github.com/bdraco/yalexs/commit/88dbab72f6588e4e4786b204a491277b5f195998))

* Add async_status_async (#22) ([`2a5f2c4`](https://github.com/bdraco/yalexs/commit/2a5f2c4479ca1b9afade7f93f1f0e058ac252548))


## v1.1.17 (2022-01-08)

### Unknown

* Bump version: 1.1.16 → 1.1.17 ([`2087a47`](https://github.com/bdraco/yalexs/commit/2087a47462ec6f8b8a0be5d8b696a95c9a4903e8))

* Improve august lock/unlock reliablity when api is slow (#21) ([`710fce2`](https://github.com/bdraco/yalexs/commit/710fce22873b2165d7eb17a983e4d975c6828347))


## v1.1.16 (2021-12-24)

### Unknown

* Bump version: 1.1.15 → 1.1.16 ([`f444315`](https://github.com/bdraco/yalexs/commit/f444315e10fb464e7546378ee79f74a828f7aaa6))

* Guard against empty pubnub callback on disconnect (#20) ([`64465e9`](https://github.com/bdraco/yalexs/commit/64465e9a664ea367499eb50bec62f311fb6f7cb6))


## v1.1.15 (2021-12-17)

### Unknown

* Bump version: 1.1.14 → 1.1.15 ([`e4d51c8`](https://github.com/bdraco/yalexs/commit/e4d51c8117c5f50b2d4797caef83c74e53e0c11f))

* Add support for the DoorbellImageCaptureActivity to update_doorbell_image_from_activity (#19) ([`924b5cf`](https://github.com/bdraco/yalexs/commit/924b5cf282818ce4aff59d27d7ecc52f41a70c93))


## v1.1.14 (2021-12-17)

### Unknown

* Bump version: 1.1.13 → 1.1.14 ([`b24bf39`](https://github.com/bdraco/yalexs/commit/b24bf3910c336f87b115a3dcdb52429dcbe55f9d))

* BREAKING CHANGE: Split motion and imagecapture into separate activities (#18) ([`f27758a`](https://github.com/bdraco/yalexs/commit/f27758a23085cb3b5b98095dc8fc9c7003cc4a08))


## v1.1.13 (2021-07-28)

### Unknown

* Bump version: 1.1.12 → 1.1.13 ([`99c243f`](https://github.com/bdraco/yalexs/commit/99c243fc6f10421adc6f886359123309523152c9))

* Add new state LockDoorStatus.DISABLED for when doorsense is explicitly disabled (#15) ([`aa2bf72`](https://github.com/bdraco/yalexs/commit/aa2bf72047614598d32116ad01350c8d14bf1e9c))

* Remove python 3.10 alpha from the CI (#16) ([`be24643`](https://github.com/bdraco/yalexs/commit/be24643473850027270fbfa3c32b7cd951a3a3d6))


## v1.1.12 (2021-07-10)

### Unknown

* Bump version: 1.1.11 → 1.1.12 ([`d5c8075`](https://github.com/bdraco/yalexs/commit/d5c8075905fe8380e8ce462dfa2aaf5541136415))

* Bump version: 1.1.10 → 1.1.11 ([`e1a57b2`](https://github.com/bdraco/yalexs/commit/e1a57b2578be3f8c87aec7082345f98a8086c1e3))

* Fix isort in test (#14) ([`d548b9a`](https://github.com/bdraco/yalexs/commit/d548b9afa1d460f9fbda962b8af365baf5c7590d))

* Add support for unlocking and jammed status (#13) ([`b952d81`](https://github.com/bdraco/yalexs/commit/b952d81f039a5b37387e3e122d9ee59c47b237a0))

* Handle initial LockStatus missing (#12) ([`cf9cab6`](https://github.com/bdraco/yalexs/commit/cf9cab63a8008e1728b4c9ac446253c4a464ba1e))


## v1.1.10 (2021-03-30)

### Unknown

* Bump version: 1.1.9 → 1.1.10 ([`afc93f6`](https://github.com/bdraco/yalexs/commit/afc93f60eda6e8a9810e82582811316b7a1d6b4f))

* Revert pubnub reconnect workaround and update to pubnub 5.1.1 (#11) ([`be95829`](https://github.com/bdraco/yalexs/commit/be95829ec1e6e6092501cb189390e60c17f54be2))


## v1.1.9 (2021-03-27)

### Unknown

* Bump version: 1.1.8 → 1.1.9 ([`b597dbf`](https://github.com/bdraco/yalexs/commit/b597dbf6f703667a3898c971dd2d6176e54a9da0))

* Change pubnub version to &gt;=5.1.0 (#10) ([`b790850`](https://github.com/bdraco/yalexs/commit/b7908503b08dc00c531c6b5725e6cfdfdfbeaf7e))


## v1.1.8 (2021-03-27)

### Unknown

* Bump version: 1.1.7 → 1.1.8 ([`8d980af`](https://github.com/bdraco/yalexs/commit/8d980af4b9c42be9d55a08fa0051329e7c6daccc))

* Workaround pubnub reconnect bug (#9) ([`7fc8039`](https://github.com/bdraco/yalexs/commit/7fc803928c21e3d51a6efd1edd729ed68ddbc545))


## v1.1.7 (2021-03-27)

### Unknown

* Bump version: 1.1.6 → 1.1.7 ([`d279972`](https://github.com/bdraco/yalexs/commit/d279972593df8059aab058f6276d440111b34a05))

* Always reconnect on unknown errors (#8) ([`9b9af69`](https://github.com/bdraco/yalexs/commit/9b9af69dfb4709d92b031acff60b8ddb7b526d5f))


## v1.1.6 (2021-03-26)

### Unknown

* Bump version: 1.1.5 → 1.1.6 ([`39a74c2`](https://github.com/bdraco/yalexs/commit/39a74c2a5740a915c4d4beef19df5036ffb9ad9d))

* Improve pubnub reconnect logic (#7) ([`7927614`](https://github.com/bdraco/yalexs/commit/792761495a62e7058365be94bbbce747d5d258cd))


## v1.1.5 (2021-03-22)

### Unknown

* Bump version: 1.1.4 → 1.1.5 ([`56d108a`](https://github.com/bdraco/yalexs/commit/56d108abb1de9655612953f43c87968f5b468d03))

* Ensure pubnub reconnects on outage (#6) ([`993a93c`](https://github.com/bdraco/yalexs/commit/993a93cb05e1fb1ba6ba3c27001111617d91a297))


## v1.1.4 (2021-03-21)

### Unknown

* Bump version: 1.1.3 → 1.1.4 ([`89b40b3`](https://github.com/bdraco/yalexs/commit/89b40b3ea1c0c8defd59f5e11710b72e1c6cf21e))

* Do not store operator for pubnub (#5) ([`dd44b3b`](https://github.com/bdraco/yalexs/commit/dd44b3b875091b1b5f2bfbbbde48ec425cedf1d3))


## v1.1.3 (2021-03-21)

### Unknown

* Bump version: 1.1.2 → 1.1.3 ([`c6d3ca4`](https://github.com/bdraco/yalexs/commit/c6d3ca440075c462a28e556dcf395cc5bef681c6))

* Include the activity source to allow the log to always win (#4) ([`4129ed9`](https://github.com/bdraco/yalexs/commit/4129ed998cc7fef3cb169b13c886e5935ee9e3cf))


## v1.1.2 (2021-03-21)

### Unknown

* Bump version: 1.1.1 → 1.1.2 ([`37791de`](https://github.com/bdraco/yalexs/commit/37791dea71aae803b833b9d091cfe807f973898d))

* Do not inject the user, always get it from activity since pubnub is the caller not the operator (#3) ([`0e9b86e`](https://github.com/bdraco/yalexs/commit/0e9b86e4877ffb6f4d3d6eb22866be0080a17467))


## v1.1.1 (2021-03-21)

### Unknown

* Bump version: 1.1.0 → 1.1.1 ([`45fef09`](https://github.com/bdraco/yalexs/commit/45fef096f837d60229366824eb112bea5f040786))

* Handle pubnub messages without an operator (#2) ([`aca82e1`](https://github.com/bdraco/yalexs/commit/aca82e17fc64b07088f1dbcb862a8e40bfe7553a))


## v1.1.0 (2021-03-21)

### Unknown

* Bump version: 1.0.3 → 1.1.0 ([`9f79b0b`](https://github.com/bdraco/yalexs/commit/9f79b0b6c54a06b90bd507688b45442ed368de61))

* Switch to creating activities from pubnub (#1) ([`849532f`](https://github.com/bdraco/yalexs/commit/849532fac134d0d5de36a3bde284926350d30a73))


## v1.0.3 (2021-03-20)

### Unknown

* Bump version: 1.0.2 → 1.0.3 ([`b04cda3`](https://github.com/bdraco/yalexs/commit/b04cda3ea4f068ad91ff52376fef0f500f01ae1f))

* Switch to setuptools ([`aea8963`](https://github.com/bdraco/yalexs/commit/aea8963c0f24cf7043bd5b0e2af1e51d6a77e858))


## v1.0.2 (2021-03-20)

### Unknown

* Bump version: 1.0.1 → 1.0.2 ([`9b14523`](https://github.com/bdraco/yalexs/commit/9b1452300bfe73e3bc462dedbcf59384d8802cd5))

* Tweaks to setup.py ([`c0f467e`](https://github.com/bdraco/yalexs/commit/c0f467ecfcb8fcfd40a9ea79ddbe933b8ba32b70))

* Tweaks to setup.py ([`fc40662`](https://github.com/bdraco/yalexs/commit/fc4066232371e0c8e21806c4259cbcd846418f97))

* Fix CI ([`bad669d`](https://github.com/bdraco/yalexs/commit/bad669de938fc031a81addf18555878cc8fa323e))

* format black ([`4ad6634`](https://github.com/bdraco/yalexs/commit/4ad6634975b9243190df831f0fcd332b282daab7))

* Cleanup setup.py ([`b16e789`](https://github.com/bdraco/yalexs/commit/b16e7892838a0680070f67ad219cdb454342c7ea))

* Add build.sh ([`9946a3e`](https://github.com/bdraco/yalexs/commit/9946a3efb1f29d4bd86a7565d87949b36a30fa60))


## v1.0.1 (2021-03-20)

### Unknown

* Bump version: 1.0.0 → 1.0.1 ([`8ef8c3a`](https://github.com/bdraco/yalexs/commit/8ef8c3af1bf21be7d1e91432fb2170bb2aa8d3b1))

* Bumpversion ([`4ee92c7`](https://github.com/bdraco/yalexs/commit/4ee92c72715bbd7140c6083cf5e52b2b672039ff))

* Bumpversion ([`6feebd1`](https://github.com/bdraco/yalexs/commit/6feebd16e0660c629ed8b55de95b9254084394a4))

* Rename to yalexs ([`2e7e619`](https://github.com/bdraco/yalexs/commit/2e7e6198e5e95ecb12a37d86c379bbf995207093))

* Add basic pubnub support ([`1d2b17b`](https://github.com/bdraco/yalexs/commit/1d2b17b2b596e993981481dc92daaf2b6d91452e))

* Fix CI and switch to GH actions ([`707f9b9`](https://github.com/bdraco/yalexs/commit/707f9b96194322d17152e707ba174eb7a775f07a))

* Merge pull request #56 from ai-write-city/master

Bumped version to 0.25.2 ([`78b25da`](https://github.com/bdraco/yalexs/commit/78b25da03194d68d70115f36bf926a3a6443e555))

* Bumped version to 0.25.2 ([`5b3b539`](https://github.com/bdraco/yalexs/commit/5b3b539851dea7f166eb93f7abb5de6283b15e46))

* Merge pull request #55 from ai-write-city/master

Bumped version to 0.25.1 + fix build ([`30f77e8`](https://github.com/bdraco/yalexs/commit/30f77e8d59e7d37e44b35601b7c7ec5320ee649b))

* Fixed incorrect dep (dateutil -&gt; python-dateutil)
Fixed lint error ([`cc695f6`](https://github.com/bdraco/yalexs/commit/cc695f67eef46ba12cd93e232c24e9a9e264dfb6))

* Merge branch &#39;master&#39; of github.com:ai-write-city/py-august ([`f0d6af6`](https://github.com/bdraco/yalexs/commit/f0d6af65ec94dc5b91e6b2e5bd456eec5f785ccf))

* Merge pull request #1 from snjoetw/master

Merge in from upstream ([`6fef771`](https://github.com/bdraco/yalexs/commit/6fef771a091aa2098c7e45af068332c6acfc76a5))

* Bump version to 0.25.1 ([`c79b0d5`](https://github.com/bdraco/yalexs/commit/c79b0d5b0de3c0d54e85d14eafee7c93bcbddafc))

* Merge pull request #54 from ai-write-city/master

Fixed lint warnings ([`fdd7e82`](https://github.com/bdraco/yalexs/commit/fdd7e828179f252c9b3e2c5465f37f428950ea64))

* Fixed lint warnings ([`6704a4c`](https://github.com/bdraco/yalexs/commit/6704a4c50c01c32c62e49cd60222f9b50df54b1d))

* Merge pull request #52 from fabaff/patch-1

Add dateutil ([`e8b875d`](https://github.com/bdraco/yalexs/commit/e8b875d08720ae507e4657cfcfeb01b347d12aeb))

* Merge pull request #50 from bdraco/fix_token_refresh

Fix august token refresh ([`61ab1cf`](https://github.com/bdraco/yalexs/commit/61ab1cf3a911d4651eba733faa6667cd1fd12c07))

* Add dateutil ([`d734dbb`](https://github.com/bdraco/yalexs/commit/d734dbbd09a76b3c690d07d0f24a59833845542e))

* Fix august token refresh ([`90046a8`](https://github.com/bdraco/yalexs/commit/90046a8c514b0e079c8cfbe61a35990546537de2))

* Merge pull request #48 from bdraco/fix_validation_and_add_tests

Fix validation code verification passing login_method as a string instead of var ([`a8eb0df`](https://github.com/bdraco/yalexs/commit/a8eb0df53bacc21999ae8172bc4ab8f1df4b9b9f))

* Fix validation code verification passing login_method as a string instead of a var ([`adc6718`](https://github.com/bdraco/yalexs/commit/adc6718d17b9406e89a8011e5f95d5216a55edeb))

* Merge pull request #47 from bdraco/operation_details

Add additional details to the Lock activity ([`3556550`](https://github.com/bdraco/yalexs/commit/35565506601e1a3e99f77ae21ec20cab9cb58c1f))

* Merge pull request #46 from bdraco/add_async_api

Add async support ([`dee8716`](https://github.com/bdraco/yalexs/commit/dee87163949d554de09bb01fc61073ad2de16999))

* Add additional details to the Lock activity

* Lock operation was remote

* Lock operation was done via keypad

* Lock operation done by autorelock

* Lock operator image url

* Lock operator thumbnail url ([`d11777b`](https://github.com/bdraco/yalexs/commit/d11777b98641e0c0d92ad82f1d8c85edb1ed9af0))

* Add async support

This adds support for working with the august api with async

The existing non-async support is left in-tact and it now shares
a common base module for Api and Authenticator to ensure
backwards compat.

When using async, the following changes need to be made in your
code

Api is now ApiAsync

  ApiAsync must be passed an aiohttp ClientSession()
  as the first argument

  await async_setup() must be called to setup the object
  after creating it

Authenticator is now AuthenticatorAsync

  AuthenticatorAsync must be passed an aiohttp ClientSession()
  as the first argument

  await async_setup_authentication() must be called to setup
  the object

AugustApiHTTPError is replaced with AugustApiAIOHTTPError

Checking for RequestException is replaced with checking for
ClientError

All of the async functions are prefixed with async_
Ex get_operable_locks is now async_get_operable_locks ([`f984e8d`](https://github.com/bdraco/yalexs/commit/f984e8da024a4305bba7f837a25a3a72056f06e4))

* Merge pull request #45 from bdraco/gen2_battery

Additional battery percentage estimations ([`87dd062`](https://github.com/bdraco/yalexs/commit/87dd0621bdf8e6b00988925e5b8c39f2bc62fc22))

* Additional battery percentage estimations

* Battery percentage for the mars2 lock

* Battery percentage for the keypad

These mirror the name to percentage mappings
currently used in home assistant ([`e6eaa3e`](https://github.com/bdraco/yalexs/commit/e6eaa3ed3ee5d5e49369f8d0bb63f0e1a4d316a5))

* Merge pull request #44 from bdraco/add_offline_doorbell_tests

Add offline doorbell tests ([`9adeef6`](https://github.com/bdraco/yalexs/commit/9adeef67dc9e6c3f731a58183881ddd6e22d6bb9))

* Merge pull request #43 from bdraco/expose_model

Expose model and keypad name ([`2c58436`](https://github.com/bdraco/yalexs/commit/2c584365d8122a27fb0a447a7e306dac748197e2))

* Merge pull request #42 from bdraco/bridge_is_online

Bridge is online ([`3579532`](https://github.com/bdraco/yalexs/commit/3579532e2aa2a7cc49db8eebb70d5b10886edec2))

* Merge pull request #41 from bdraco/doorbell_image_fetch

Doorbell image fetch ([`8688e8e`](https://github.com/bdraco/yalexs/commit/8688e8ecf0b17947e18eb7151ce9de40555ae2b9))

* Add tests for offline doorbells ([`ba4d8dd`](https://github.com/bdraco/yalexs/commit/ba4d8dd1ca52a31eb28f76b3b016a8e57cdf3411))

* Expose model and keypad name

Homeassistant uses this information in the device
registry:

https://developers.home-assistant.io/docs/device_registry_index/

This is the final piece needed to convert august to config_flow ([`ee1909d`](https://github.com/bdraco/yalexs/commit/ee1909dc504d9121f97e9f094fd1ac817df81c90))

* Merge pull request #40 from bdraco/doorbell_image_updates_from_activity

Add ability to update doorbell images from activity ([`860c2cc`](https://github.com/bdraco/yalexs/commit/860c2cc55d6dd1ada4b7d935fc784072c0f72b1e))

* Add a bridge_is_online property to LockDetail

This allows us to normalize reporting of available
status in homeassistant ([`5ef620f`](https://github.com/bdraco/yalexs/commit/5ef620f8613eaa1d042caa35b6429f5f608a395c))

* Add support for fetching the doorbell image

Homeassistant wants all requests handled in
the py-august module ([`1e86023`](https://github.com/bdraco/yalexs/commit/1e86023f9254699bd3bb994cace79b775f2d9d1f))

* Add ability to update doorbell images from activity

* Fix tests for doors when timezone is not utc

* Add check for standby status to doorbells so they do not
  unexpectedly get marked unavailable ([`e99e939`](https://github.com/bdraco/yalexs/commit/e99e939cd01bdc21798ee37dc2d575af3f4c6b33))

* Merge pull request #39 from bdraco/lock_with_detail_so_we_can_get_door_state_sq

Add lock_return_activity and unlock_return_activity apis (additional reduction in august api calls) ([`f41a3a9`](https://github.com/bdraco/yalexs/commit/f41a3a97b82922f517df749250e8f3839e6f918b))

* Merge pull request #38 from bdraco/update_lock_detail_with_activity

Update lock detail with activity ([`13d2a55`](https://github.com/bdraco/yalexs/commit/13d2a550fc0a09a304a34ff98d5d7ae4a7347325))

* Merge pull request #37 from bdraco/add_status_info_to_detail_to_avoid_multiple_api_calls

Add door status to lock detail ([`e417c71`](https://github.com/bdraco/yalexs/commit/e417c71c1ccd2fb87cb61e751f494037912c079c))

* Add lock_return_activity and unlock_return_activity apis

It is now possible to call the lock and unlock remote operation
and get back a LockOperationActivity that can be consumed by
update_lock_detail_from_activity.  If the lock supports doorsense,
a DoorOperationActivity is also returned since the underlying
August API returns this.

Lock operations now avoid the need to fetch lock details afterward
which further reduces the number of API calls we make to the
August API ([`78078dc`](https://github.com/bdraco/yalexs/commit/78078dcd5d4061f128c02757014d763f5f6a5cb4))

* Provide a util to update LockDetail from activity

Home Assistant checks the activity log far more frequently than other
apis in order to reduce the number of api calls.

The new update_lock_from_activity util provides a way to update a
LockDetail class with one of the following activities:

  LockOperationActivity
  DoorOperationActivity ([`24b08ee`](https://github.com/bdraco/yalexs/commit/24b08ee13f503be9242a3c10adf476a37fb82dbb))

* Add door status to lock detail

In order to reduce the number of api calls we can
now get the door status from the single lock detail
endpoint since it is contained inside the detail api.

Provide sets for the lock status and door state in
the LockDetail so they can be updated with data
from the activity api ([`6beafb0`](https://github.com/bdraco/yalexs/commit/6beafb0e1a22de1242ad9448ad1b94dbf64a55de))

* - fixed lint error ([`8a0f029`](https://github.com/bdraco/yalexs/commit/8a0f029045be823ba415672d5804c5f2c0dc9be5))

* Merge pull request #35 from bdraco/hide_implementation_details_behind_exception

Hide implementation details with exceptions ([`7089897`](https://github.com/bdraco/yalexs/commit/7089897415e1b1809fa2bc07ce879e1efa59d287))

* Merge pull request #36 from bdraco/handle_doorsense_in_init_state

Handle doorsense in &#34;init&#34; state (should be set to false) ([`75eedb0`](https://github.com/bdraco/yalexs/commit/75eedb0461cc900a5b62ee23f3aa654c47447f75))

* Handle doorsense in &#34;init&#34; state (should be set to false) ([`402e74e`](https://github.com/bdraco/yalexs/commit/402e74ed6b13e60b6870c4dd4a6d2451860d93d0))

* Hide implementation behind exceptions

The exceptions returned from the api requests should
be more helpful to users so they can figure out how
to resolve them.  Home assistant has issues opened
when a bridge if offline or unavailable because users
do not understand the exception being provided. ([`ec5904b`](https://github.com/bdraco/yalexs/commit/ec5904bac64247a1108caeaa73ebb527b84a3366))

* Merge pull request #33 from bdraco/bridge_and_doorsense

Expose bridge information and if doorsense is installed ([`d7e1756`](https://github.com/bdraco/yalexs/commit/d7e1756870a65d42ef94926d44376629b665bde2))

* Merge pull request #34 from bdraco/doorbell_battery_level

Expose the battery level for doorbells ([`d8dfd2e`](https://github.com/bdraco/yalexs/commit/d8dfd2e3118525f371b7bae967e8763f6342067e))

* Expose the battery level for doorbells ([`0099e14`](https://github.com/bdraco/yalexs/commit/0099e1438172aeb1659a6f9b3be36f2c55acf663))

* black ([`203a0ad`](https://github.com/bdraco/yalexs/commit/203a0ad1c274d2f0ec4aa1db83bd876a570b2898))

* bol ([`8f954e5`](https://github.com/bdraco/yalexs/commit/8f954e5b3086825dbc23980e1db689353db937c7))

* bump ([`3c9fe51`](https://github.com/bdraco/yalexs/commit/3c9fe51d233665483a55fdbd9eabad0f1ae75316))

* more tests for bridge ([`b17d3ab`](https://github.com/bdraco/yalexs/commit/b17d3ab6aad194f90deed0cdd6777d7c7d2606f5))

* add ([`77b2370`](https://github.com/bdraco/yalexs/commit/77b2370a16e0970e21843c2468303b9d473b1e99))

* add ([`313045c`](https://github.com/bdraco/yalexs/commit/313045ce88e728ec21eaf76153d4244fb91e5ffe))

* Add bridge and doorsense properties ([`a53ca0d`](https://github.com/bdraco/yalexs/commit/a53ca0ddb4791bd36c50567698bfc67404b090bd))

* - bumped version to 0.12.0 ([`73420f0`](https://github.com/bdraco/yalexs/commit/73420f05174f867b11cb0fbc71178de284696fdc))

* - updated tox to use py36 and 37 ([`ecba2e1`](https://github.com/bdraco/yalexs/commit/ecba2e1d3c1233e76e8a987049d8709ae39ae5f7))

* - fixed flake8 errors ([`c32e37f`](https://github.com/bdraco/yalexs/commit/c32e37fda8d482a1aa6a066a047acf2178d4de2d))

* Merge pull request #31 from bdraco/const_for_actions

Add documentation and tests for new actions in activities ([`56b717b`](https://github.com/bdraco/yalexs/commit/56b717bdfb16168eac2942553a3b9ab9dde0f158))

* Merge pull request #32 from bdraco/add_missing_dateutil

Add missing python-dateutil to setup.py ([`961aded`](https://github.com/bdraco/yalexs/commit/961aded38c228e5f38638dbb7675f78e9985cc98))

* Add missing python-dateutil to setup.py ([`ebf0a16`](https://github.com/bdraco/yalexs/commit/ebf0a163fcd127df6b1a77d8608688458b4e3379))

* Merge branch &#39;docs_for_activity&#39; into const_for_actions ([`cdd90ff`](https://github.com/bdraco/yalexs/commit/cdd90ff13392b83b49725c460e8f599935df627a))

* Add tests for get_house_activities ([`1ebd906`](https://github.com/bdraco/yalexs/commit/1ebd90684a05e1b622f68a4b08e44810be0a6fa2))

* add activity tests ([`8f8ce77`](https://github.com/bdraco/yalexs/commit/8f8ce77128efc4c7a234c20197ed127dfffd76ff))

* sort ([`f71fee2`](https://github.com/bdraco/yalexs/commit/f71fee236927f62ee1dcbf17ef32e3b874ff1e64))

* Add ACTIVITY_ACTION_STATES ([`506a8a3`](https://github.com/bdraco/yalexs/commit/506a8a31d9b686e96322fdfe1c7aa530d3237450))

* Add constants for actions ([`da020cb`](https://github.com/bdraco/yalexs/commit/da020cb244e9ae291723c41d1a3752a034014909))

* Keep track of known activities in
known_activities.md ([`1cea295`](https://github.com/bdraco/yalexs/commit/1cea2958d5cf6550de6a1aded9d02ff982633c5e))

* - bumped version to 0.11.0 ([`3e2a646`](https://github.com/bdraco/yalexs/commit/3e2a646c9df9c9f092536715bf56e90b1391cce1))

* - fixed flake8 error ([`079ba2b`](https://github.com/bdraco/yalexs/commit/079ba2b6c138b03a6659756f6736bd595662300a))

* Merge pull request #30 from bdraco/fix_timezone_compare_on_token_refresh

Make sure the expire time we get back from the ([`4fd857a`](https://github.com/bdraco/yalexs/commit/4fd857aa66d0807698af99a848e58955cdebbe10))

* Merge pull request #29 from bdraco/doorsense_support

Add support for doorsense to the activity module ([`752dc8e`](https://github.com/bdraco/yalexs/commit/752dc8eae272cee76afd56f68d152c5924af28f5))

* Merge pull request #28 from bdraco/onetouchlock

Add support for onetouchlock ([`4c2662e`](https://github.com/bdraco/yalexs/commit/4c2662e654c322f039b42ccad0bfda65c9837aef))

* Make sure the expire time we get back from the
refresh api has a timezone so we are consistent for other
comparisons ([`f9c4cf4`](https://github.com/bdraco/yalexs/commit/f9c4cf49e27757bb6af66e513b24066185964055))

* Add support for doorsense to the activity module ([`3b9e86d`](https://github.com/bdraco/yalexs/commit/3b9e86d39ceb1e0fa3a20cf15bf31c040d639d4b))

* Add support for onetouchlock ([`c3d5cee`](https://github.com/bdraco/yalexs/commit/c3d5cee1b4283888ea5cd6f0d6abbad902a795ac))

* - updated travis build to only use python 3.6 and 3.7 ([`92eab92`](https://github.com/bdraco/yalexs/commit/92eab92a8abe3d05f8bd49fb5d48e116976f7665))

* - fixed test ([`18f2682`](https://github.com/bdraco/yalexs/commit/18f2682fbfb0ace16d5b1fdc6e47679bf51a85c5))

* - bumped version to 0.10.1 ([`dfe8347`](https://github.com/bdraco/yalexs/commit/dfe8347afb9b970b289b78fad9f64336f9ca156a))

* Merge pull request #25 from bdraco/fix_timezone_compare

Get time with a timezone. ([`3f5e94a`](https://github.com/bdraco/yalexs/commit/3f5e94abee6c87add6e6605f93412d43f5ecd1f0))

* - fixed lint and flake8 errors ([`3bbe9ea`](https://github.com/bdraco/yalexs/commit/3bbe9eab664d9547fd86df8962d38c6305d20bc3))

* Get time with a timezone.

Fixes:

Traceback (most recent call last):
  File &#34;/usr/src/homeassistant/homeassistant/setup.py&#34;, line 174, in
_async_setup_component
    component.setup, hass, processed_config  # type: ignore
  File &#34;/usr/local/lib/python3.7/concurrent/futures/thread.py&#34;, line 57,
in run
    result = self.fn(*self.args, **self.kwargs)
  File &#34;/config/custom_components/august/__init__.py&#34;, line 161, in
setup
    access_token_cache_file=hass.config.path(AUGUST_CONFIG_FILE),
  File &#34;/usr/local/lib/python3.7/site-packages/august/authenticator.py&#34;,
line 110, in __init__
    if self._authentication.is_expired():
  File &#34;/usr/local/lib/python3.7/site-packages/august/authenticator.py&#34;,
line 76, in is_expired
    return self.parsed_expiration_time() &lt; datetime.utcnow()
TypeError: can&#39;t compare offset-naive and offset-aware datetimes ([`c872aee`](https://github.com/bdraco/yalexs/commit/c872aee2cc4bb108676bcfa06f0822e38c68a956))

* - fixed lint errors ([`84001fc`](https://github.com/bdraco/yalexs/commit/84001fc59495763418d87039c56f6bfbffd83c19))

* - bumped version to 0.10.0 ([`e51354d`](https://github.com/bdraco/yalexs/commit/e51354d6e0a6254d689320d79023b737efe6fc2b))

* - bumped version to 0.9.0 ([`b45747e`](https://github.com/bdraco/yalexs/commit/b45747ed6b80be4f0e5df0f57fc9522444127155))

* Merge pull request #23 from sidoh/refresh_access_token

Add support for refreshing access token ([`052a50c`](https://github.com/bdraco/yalexs/commit/052a50c2d0de64551ba67fd221bc3d656d50e65f))

* Merge pull request #24 from bdraco/handle_429

Handle 429 ([`fb76d0d`](https://github.com/bdraco/yalexs/commit/fb76d0d815f6abc329c1ba0fbb08c3a905dd830f))

* tweak timing ([`f434de6`](https://github.com/bdraco/yalexs/commit/f434de6b3c407d42b60bfa4255c9e9b8da46941c))

* try harder ([`281147c`](https://github.com/bdraco/yalexs/commit/281147c80d15c641ff1e8c8ebff7f5eb3542f408))

* Handle 429 from august ([`9fb029a`](https://github.com/bdraco/yalexs/commit/9fb029ad83526afa1c9ca3e5269d9283b1774f67))

* Ignore .vscode ([`c6150c2`](https://github.com/bdraco/yalexs/commit/c6150c2becbde58481c41dc228e4118fa4de7184))

* add test ([`53e86f3`](https://github.com/bdraco/yalexs/commit/53e86f378df99a91ad0fa0cf366e15092e15f479))

* Add methods to auto-refresh access token ([`c89c4a2`](https://github.com/bdraco/yalexs/commit/c89c4a248cf4d6f594441254bb4c295044286fda))

* Add method to get new access token from API ([`3ff3183`](https://github.com/bdraco/yalexs/commit/3ff3183c6103dffe7394ebe1671692b6ebbc1612))

* Merge pull request #21 from aijayadams/master

Set install_requires for pip deps ([`b5a7c98`](https://github.com/bdraco/yalexs/commit/b5a7c9849253b8c556f175592102d1d8b84f0f28))

* Set install_requires for pip deps ([`e79516c`](https://github.com/bdraco/yalexs/commit/e79516c213fd57adb97d1c48347bdda85a6f7d14))

* - fix lint error ([`f777ccf`](https://github.com/bdraco/yalexs/commit/f777ccf93d5f0918e08859392be29e92f89e9bd3))

* - refactored pin.py to fix lint error
- added test for get_pins API ([`02d62a8`](https://github.com/bdraco/yalexs/commit/02d62a8f127ce5ef47d971c5cc5d46f8f37b930b))

* - fixed lint error ([`0605e85`](https://github.com/bdraco/yalexs/commit/0605e858d29161e9e32deebe1d7877c9d1313713))

* Merge pull request #17 from msmeeks/api-usage-readme

Add example Api usage to the README ([`1ea9cc2`](https://github.com/bdraco/yalexs/commit/1ea9cc20ed0da6b67ebd3f3e8853e9fdbb988fa3))

* Merge pull request #15 from ehendrix23/Fix-token-expired

Check if token is expired ([`67279d0`](https://github.com/bdraco/yalexs/commit/67279d0c78c779bbe6d786024fa84179e4ff1a9d))

* Add example Api usage to the README ([`5f10723`](https://github.com/bdraco/yalexs/commit/5f10723d85a729e3e1667154bbce9d4e9fc95474))

* Check if token is expired

Check if token is expired or will almost expire. If token expires within 7 days then log a warning, if token is expired then log an error.
If token is expired then also set state that authentication is required. ([`9221c0c`](https://github.com/bdraco/yalexs/commit/9221c0cc132c77956a45b2f375542b17dbb64006))

* bump up version to 0.7.0 ([`f08e0c7`](https://github.com/bdraco/yalexs/commit/f08e0c7d7c0ca8049e192f43d5fa047c700cbff8))

* Merge pull request #11 from ehendrix23/Use-Session-and-combine-lock-with-door-status

Use session and combine lock with door status ([`1dc9bc3`](https://github.com/bdraco/yalexs/commit/1dc9bc331d4f32e748140e810d869f99afe081fd))

* Merge pull request #12 from rjames86/rm-keypad-pins

Adding support for lock keypads and get pins ([`48064ae`](https://github.com/bdraco/yalexs/commit/48064ae8ab1c44a85c16caf2327fac9981c94aba))

* remove print statement ([`b44a954`](https://github.com/bdraco/yalexs/commit/b44a9544809e63ce63ed05aef8cdaaa75ccf78b6))

* adding support for lock keypads and get pins ([`61ce49d`](https://github.com/bdraco/yalexs/commit/61ce49d8a5a45b137108eb4f49b5e23daad331c1))

* Request Session as parameter

Changed to have the Request.Session be a parameter as part of init instead of creating it within the API itself. This way no need to worry about closing it as it is the responsibility of the calling program to do so. ([`84d6749`](https://github.com/bdraco/yalexs/commit/84d67495d54d2dd9e6aff8fc7e5d1d75a2e8d2bd))

* Additional comment for the close method

Added additional comment to clarify the close method. ([`db342ec`](https://github.com/bdraco/yalexs/commit/db342ec032b4e7050f6164e42673338096e54662))

* Add Session and support for retrieving door&amp;lock status together

Add option to use session allowing for re-using the TCP connection.
Add option to retrieve the door status together with lock (or lock together with door) if both are wanted. ([`1ab4dc7`](https://github.com/bdraco/yalexs/commit/1ab4dc76a4bba319ca1d818fb18226af7b47c8b3))

* Bumped version to 0.6.0 ([`2f6f4dc`](https://github.com/bdraco/yalexs/commit/2f6f4dc56587ed86285d7bf4161001f39b07f653))

* Fixed failing tests ([`3c5fce6`](https://github.com/bdraco/yalexs/commit/3c5fce601cf3c8940fb1bd6134acb33fc90aa421))

* Addressed lint warning ([`f52b811`](https://github.com/bdraco/yalexs/commit/f52b811cd8144989a424f4e62713d3fc0480bb65))

* Updated api key as mention in #6 ([`688ed4e`](https://github.com/bdraco/yalexs/commit/688ed4e3727447109868d4ed848f3bedc99a00db))

* Bumped version 0.5.0 ([`edaadc3`](https://github.com/bdraco/yalexs/commit/edaadc3c550f6b201fc2597207406183bb84d1d6))

* Fixed lint errors in tests ([`d378cdc`](https://github.com/bdraco/yalexs/commit/d378cdcab0c61c174b8957bcca3d2cb820d0737d))

* Fixed lint errors ([`40e9c16`](https://github.com/bdraco/yalexs/commit/40e9c16174f2a8c26399c9be836c42442ddeb9da))

* Merge pull request #4 from sfiorini/master

Added Lock Door Status (August DoorSense) ([`643253f`](https://github.com/bdraco/yalexs/commit/643253f593b348a882e352337a9a8754269c086b))

* Added missing import for LockDoorStatus. ([`ce4d4e4`](https://github.com/bdraco/yalexs/commit/ce4d4e4cb3ea0368387518a93321c680735c90a4))

* Updated fixture to return door state attribute. ([`fc6f979`](https://github.com/bdraco/yalexs/commit/fc6f979f83cf90ce180728f290daa0a2f4aff214))

* Added tests for Lock Door Status. ([`c0e4c40`](https://github.com/bdraco/yalexs/commit/c0e4c4094d4c50547d3d3f3a79a54e65deb60ded))

* Added method to retrieve lock door status (&#34;DoorSense&#34; sensor) ([`988dac8`](https://github.com/bdraco/yalexs/commit/988dac8d40c4af179a6f97a1a21d12253de08fd3))

* Bumped up version to 0.4.0 ([`0d743d5`](https://github.com/bdraco/yalexs/commit/0d743d52200e4919e95491027b6969d74bc79767))

* Fixed https://github.com/snjoetw/py-august/issues/1

- Added get_operable_locks() API to only include locks owned by superuser ([`e1004e7`](https://github.com/bdraco/yalexs/commit/e1004e758ef1cf3958be6b7c06dfb3d010d7d386))

* - Updated MANIFEST ([`443c5a9`](https://github.com/bdraco/yalexs/commit/443c5a9b7877f3d35de65989129705202d48e2f2))

* - Bumped version to 0.3.0 ([`13c98ad`](https://github.com/bdraco/yalexs/commit/13c98ad1ccef834a03c9b06f13329e0cd0bda8f4))

* - Fixed pylint error ([`360bb23`](https://github.com/bdraco/yalexs/commit/360bb232c5f5e7746590e5cdad6a1124c986711b))

* - Deleted august.py ([`976ca0c`](https://github.com/bdraco/yalexs/commit/976ca0c8ab607a98f934996a4f7243dd8baddb6c))

* - Added __init__.py ([`4d1c8f9`](https://github.com/bdraco/yalexs/commit/4d1c8f99736f0a69727b4329b3ee0c559563dbba))

* - Fixed incorrect lock status handling ([`6b53424`](https://github.com/bdraco/yalexs/commit/6b5342414eaa387cc6834d3ef18df13f9b4a0412))

* - Added LockOperationActivity ([`b1fc3bc`](https://github.com/bdraco/yalexs/commit/b1fc3bc34bc594fcd26b7202028c6c4864143c02))

* - Renamed API method, get_lock() =&gt; get_lock_detail(), get_doorbell() =&gt; get_doorbell_detail() ([`59e2b81`](https://github.com/bdraco/yalexs/commit/59e2b8176785d184b8a97499c63befd913fbf0f6))

* - Added LockDetail and DoorbellDetail to represent more detailed device information
- Updated Api to take command_timeout so that lock/unlock can have different timeout then other GET APIs
- get_lock and get_doorbell API now returns LockDetail and DoorbellDetail
- Added is_online property to Doorbell
- Added more tests ([`cea3da5`](https://github.com/bdraco/yalexs/commit/cea3da508852381917e9c27445af7268f7dca032))

* Added August class that wraps API call with easier to use methods ([`f4edc95`](https://github.com/bdraco/yalexs/commit/f4edc95e922a48b9ff798efdde8e271405febeee))

* Added vol dependency ([`4ab7921`](https://github.com/bdraco/yalexs/commit/4ab7921a0fcb6251295e073919e87ac455be2ada))

* Merge branch &#39;master&#39; of https://github.com/snjoetw/py-august ([`1ff4d9b`](https://github.com/bdraco/yalexs/commit/1ff4d9b1bdb5bad306d725707a3965988424c3df))

* Added tests for lock related APIs ([`d14b994`](https://github.com/bdraco/yalexs/commit/d14b994c64fae8966868b2670d8b76bb22360af9))

* Added new APIs
- get_houses
- get_house(house_id)
- lock(lock_id)
- unlock(lock_id) ([`88b7b16`](https://github.com/bdraco/yalexs/commit/88b7b167471bb9a4fc94ad622f1cd476b93b4163))

* Comment cleanup ([`41b2cf7`](https://github.com/bdraco/yalexs/commit/41b2cf7846faacfb188e76b19171022f8daf92d3))

* Added Lock entity
Made Lock and Doorbell a child class of Device ([`94c0566`](https://github.com/bdraco/yalexs/commit/94c0566dcc85e91cb49c8d6516f7ae468bcb693f))

* Update README.md ([`68d1c98`](https://github.com/bdraco/yalexs/commit/68d1c986695e23d07e90a3064f1bbac11549244e))

* Merge branch &#39;master&#39; of https://github.com/snjoetw/py-august ([`79a3f04`](https://github.com/bdraco/yalexs/commit/79a3f04a01f157a002aa789f66d7882bd0e5fb03))

* Added manifest ([`a77b7ef`](https://github.com/bdraco/yalexs/commit/a77b7efb8d10f3b41fe6cec4e5d631df1c8295e9))

* Update README.md ([`6386916`](https://github.com/bdraco/yalexs/commit/6386916ab0535b554efa67639c92db376957390a))

* Bumper version to 0.2.0 ([`8f6b78c`](https://github.com/bdraco/yalexs/commit/8f6b78c5f1ae030a1dd24334d1f3966632322919))

* Fixed pylint errors ([`160b2f8`](https://github.com/bdraco/yalexs/commit/160b2f8b501d3524c4441150c515fd975f67ccda))

* Fixed pylint errors ([`aefa3d8`](https://github.com/bdraco/yalexs/commit/aefa3d8b772efd7b00d662ba579f2a5548a2654b))

* Added .travis.yml ([`a16fff3`](https://github.com/bdraco/yalexs/commit/a16fff39ee92f7e0a657405c396b522f2291531c))

* Fixed API url length lint violation ([`096dcd7`](https://github.com/bdraco/yalexs/commit/096dcd7e96856fc476f4e2563ac1f2a6b2a13933))

* Removed authentication flow logic and let caller handle the logic
Added ValidationResult which will be returned by Authenticator.validate_verification_code(
Added tests for Authenticator ([`bf9c43f`](https://github.com/bdraco/yalexs/commit/bf9c43f26599deeef0ff2269e10ffbb8faddc804))

* Added Api.get_doorbell(device_id) ([`4b0fbca`](https://github.com/bdraco/yalexs/commit/4b0fbca5f097256f37dafc262243550e38af12fe))

* Renamed Doorbell.id to Doorbell.device_id
Added Doorbell.has_subscription property ([`21a2085`](https://github.com/bdraco/yalexs/commit/21a20855831aacf3f5ceaac53cdc0c1b364f52d4))

* Renamed Activity.id to Activity.activity_id ([`426a7da`](https://github.com/bdraco/yalexs/commit/426a7da1c59a77ba3f2664d1329f4a4223d8adcf))

* Added build badge ([`55b6a28`](https://github.com/bdraco/yalexs/commit/55b6a28f5f114cfa8101d75fa6f9fef0b5bdda13))

* Added support for doorbell_call_initiated activity ([`c1d04ce`](https://github.com/bdraco/yalexs/commit/c1d04ce57e593ac489661f6e2cda744610e03024))

* Added Activity class
Changed get_house_activities API to return a list of Activity objects ([`d589244`](https://github.com/bdraco/yalexs/commit/d589244da97ef1f1673d1fa62b4f9af519beed15))

* Initial commit ([`5fe824b`](https://github.com/bdraco/yalexs/commit/5fe824b2fd25e303d3307ee5d677ffafae2b8bd4))

* Initial commit ([`f462999`](https://github.com/bdraco/yalexs/commit/f4629999331f8cdc157cceaebae42e4c0c1dce0f))
