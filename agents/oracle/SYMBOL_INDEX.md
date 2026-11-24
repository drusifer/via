# Codebase Symbol Index


This document lists all classes and functions in the `src/` directory with line numbers and docstrings.

Generated via AST parsing for easy code navigation.


## `src/ntag424_sdm_provisioner/card_factory.py`
- `class CardConnectionFactory` (Line 10)
  > Factory for creating card connections.
  > Switches between real hardware and simulation based on environment variables.
    - `def create` (Line 17)
      > Create a context manager that yields a card connection.

## `src/ntag424_sdm_provisioner/commands/authenticate_ev2.py`
- `class AuthenticateEV2First` (Line 21)
  > Begins the first phase of an EV2 authentication with an AES key.
  > This command requests an encrypted challenge (RndB) from the tag.
  > Response SW=91AF is expected (means "additional frame" but is actually success).
    - `def __init__` (Line 29)
    - `def __str__` (Line 33)
    - `def execute` (Line 36)
      > Execute Phase 1 of EV2 authentication.
- `class AuthenticateEV2Second` (Line 78)
  > Completes the second phase of an EV2 authentication.
  > Sends the encrypted response (RndA || RndB') to the tag and receives
  > the encrypted card response containing Ti and RndA'.
    - `def __init__` (Line 86)
    - `def __str__` (Line 92)
    - `def execute` (Line 95)
      > Execute Phase 2 of EV2 authentication.
- `class AuthenticateEV2` (Line 114)
  > EV2 Authentication orchestrator (NOT a command - it's a protocol handler).
  > This performs the two-phase EV2 authentication protocol and returns
  > an AuthenticatedConnection context manager.
  > Usage:
  > key = get_key()
  > with CardManager() as connection:
  > with AuthenticateEV2(key, key_no=0)(connection) as auth_conn:
  > # Perform authenticated operations
  > auth_conn.send(ChangeKey(...))
  > Or:
  > auth_conn = AuthenticateEV2(key, key_no=0)(connection)
  > auth_conn.send(ChangeKey(...))
    - `def __init__` (Line 133)
      > Args:
    - `def __str__` (Line 147)
    - `def __call__` (Line 150)
      > Perform complete EV2 authentication and return authenticated connection.

## `src/ntag424_sdm_provisioner/commands/base.py`
- `class Ntag424Error` (Line 18)
  > Base exception for all NTAG424 errors.
- `class ApduError` (Line 23)
  > Raised when an APDU command returns a non-OK status word.
    - `def __init__` (Line 26)
    - `def is_authentication_error` (Line 38)
      > Check if this is an authentication error.
    - `def is_permission_error` (Line 42)
      > Check if this is a permission error.
    - `def is_not_found_error` (Line 46)
      > Check if this is a not found error.
- `class AuthenticationRateLimitError` (Line 51)
  > Authentication rate-limited (0x91AD) - wait between attempts.
    - `def __init__` (Line 54)
- `class CommandLengthError` (Line 62)
  > Command length error (0x917E) - payload format issue.
    - `def __init__` (Line 65)
- `class CommandNotAllowedError` (Line 74)
  > Command not allowed (0x911C) - precondition not met.
    - `def __init__` (Line 77)
- `class SecurityNotSatisfiedError` (Line 87)
  > Security condition not satisfied (0x6985) - authentication issue.
    - `def __init__` (Line 90)
- `class AuthenticationError` (Line 101)
  > Authentication failed.
- `class PermissionError` (Line 106)
  > Permission denied for operation.
- `class ConfigurationError` (Line 111)
  > Invalid configuration.
- `class CommunicationError` (Line 116)
  > Communication with card/reader failed.
- `class AuthenticatedConnection` (Line 121)
  > Wraps a card connection with an authenticated session.
  > This class acts as a context manager and handles automatic CMAC
  > application for all authenticated commands.
  > Usage:
  > with AuthenticateEV2(key, key_no=0)(connection) as auth_conn:
  > # Use auth_conn.send() for authenticated commands
  > auth_conn.send(ChangeKey(0, new_key, old_key))
    - `def __init__` (Line 134)
      > Args:
    - `def __enter__` (Line 143)
      > Enter context manager.
    - `def __exit__` (Line 147)
      > Exit context manager.
    - `def send_apdu` (Line 152)
      > Send plain APDU without CMAC (for files with CommMode.PLAIN).
    - `def apply_cmac` (Line 167)
      > Apply CMAC to command data for authenticated commands.
    - `def encrypt_data` (Line 183)
      > Encrypt data using session encryption key.
    - `def decrypt_data` (Line 198)
      > Decrypt data using session encryption key.
    - `def encrypt_and_mac_with_header` (Line 212)
      > Encrypt data with PKCS7 padding and apply CMAC including cmd_header_data.
    - `def encrypt_and_mac` (Line 255)
      > Convenience method: Encrypt data and apply CMAC in one call.
    - `def send` (Line 287)
      > Send an authenticated command with transparent crypto (NEW PATTERN).
    - `def encrypt_and_mac_no_padding` (Line 415)
      > Encrypt and MAC for data that's already block-aligned (no PKCS7 padding).
    - `def send_authenticated_apdu` (Line 491)
      > Send an authenticated APDU with automatic CMAC application.
    - `def send_write_chunked_authenticated` (Line 544)
      > Send authenticated write with automatic chunking and crypto per chunk.
    - `def __str__` (Line 622)
- `class ApduCommand` (Line 626)
  > Abstract base class for all APDU commands.
  > This class holds the APDU structure and logic but delegates the actual
  > sending of the command to the connection object.
    - `def __init__` (Line 633)
      > Args:
    - `def build_apdu` (Line 644)
      > Build the APDU bytes for this command.
    - `def parse_response` (Line 659)
      > Parse the response from the card.
    - `def send_command` (Line 678)
      > High-level command send with automatic multi-frame handling and error checking.
- `class AuthApduCommand` (Line 748)
  > Base class for authenticated APDU commands.
  > These commands require an AuthenticatedConnection and handle crypto transparently.
  > New pattern (preferred):
  > # Command provides plaintext, connection handles crypto
  > auth_conn.send(ChangeKey(0, new_key, old_key))
  > Old pattern (deprecated):
  > # Command manages crypto explicitly
  > ChangeKey(0, new_key, old_key).execute(auth_conn)
  > Commands must implement:
  > - get_command_byte() -> int: Command byte (e.g., 0xC4 for ChangeKey)
  > - build_command_data() -> bytes: Plaintext command data
  > - parse_response() -> result: Parse decrypted response
    - `def __init__` (Line 768)
      > Args:
    - `def get_command_byte` (Line 775)
      > Get the command byte for this command.
    - `def get_unencrypted_header` (Line 789)
      > Get unencrypted header data that goes after command byte.
    - `def needs_encryption` (Line 801)
      > Indicate if command data should be encrypted.
    - `def build_command_data` (Line 811)
      > Build the plaintext command data to be encrypted.
    - `def parse_response` (Line 826)
      > Parse the decrypted response data.

## `src/ntag424_sdm_provisioner/commands/change_file_settings.py`
- `class ChangeFileSettings` (Line 12)
  > Change file settings - Unauthenticated command (no CMAC).
  > Use this for:
  > - Changing settings when Change access right = FREE
  > - Files in PLAIN mode with no auth required
  > For authenticated changes (when Change access requires a key), use ChangeFileSettingsAuth.
    - `def __init__` (Line 23)
    - `def __str__` (Line 27)
    - `def build_apdu` (Line 30)
      > Build APDU for connection.send(command) pattern.
    - `def parse_response` (Line 45)
      > Parse response for connection.send(command) pattern.
- `class ChangeFileSettingsAuth` (Line 50)
  > Change file settings - Authenticated command (with CMAC).
  > Use this when Change access right requires authentication.
  > Type-safe: Requires AuthenticatedConnection via connection.send(command).
  > Note: config.comm_mode sets the FILE's future access mode (PLAIN/MAC/FULL),
  > not the command transmission mode. This command is always authenticated.
    - `def __init__` (Line 61)
- `class ChangeFileSettings` (Line 75)
  > Change file settings - Unauthenticated command (no CMAC).
  > Use this for:
  > - Changing settings when Change access right = FREE
  > - Files in PLAIN mode with no auth required
  > For authenticated changes (when Change access requires a key), use ChangeFileSettingsAuth.
    - `def __init__` (Line 86)
    - `def __str__` (Line 90)
    - `def build_apdu` (Line 93)
      > Build APDU for connection.send(command) pattern.
    - `def parse_response` (Line 108)
      > Parse response for connection.send(command) pattern.
- `class ChangeFileSettingsAuth` (Line 113)
  > Change file settings - Authenticated command (with CMAC).
  > Use this when Change access right requires authentication.
  > Type-safe: Requires AuthenticatedConnection via connection.send(command).
  > Note: config.comm_mode sets the FILE's future access mode (PLAIN/MAC/FULL),
  > not the command transmission mode. This command is always authenticated.
    - `def __init__` (Line 124)
    - `def __str__` (Line 133)
    - `def get_command_byte` (Line 136)
      > Command byte for ChangeFileSettings.
    - `def get_unencrypted_header` (Line 140)
      > FileNo is NOT unencrypted header in ChangeFileSettings.
    - `def needs_encryption` (Line 147)
      > ChangeFileSettings is ALWAYS sent encrypted (FULL mode).
    - `def build_command_data` (Line 157)
      > Build plaintext settings payload.
    - `def parse_response` (Line 174)
      > Parse response - no data expected on success.

## `src/ntag424_sdm_provisioner/commands/change_key.py`
- `class ChangeKey` (Line 4)
  > Changes a key on the card. Must be in an authenticated state.
  > Per NXP spec: CommMode.Full is required (encryption + CMAC).
  > Key format differs for Key 0 vs other keys:
  > - Key 0: newKey + version + padding
  > - Others: (newKey XOR oldKey) + version + CRC32 + padding
  > Type-safe: execute() requires AuthenticatedConnection.
    - `def __init__` (Line 16)
    - `def __str__` (Line 23)
    - `def get_command_byte` (Line 26)
      > Get ChangeKey command byte.
    - `def get_unencrypted_header` (Line 30)
      > Get KeyNo (not encrypted, but included in CMAC).
    - `def build_command_data` (Line 34)
      > Build plaintext command data for ChangeKey.
    - `def parse_response` (Line 45)
      > Parse ChangeKey response.
    - `def _build_key_data` (Line 57)
      > Build 32-byte key data for encryption.
    - `def execute` (Line 93)
      > Execute ChangeKey command (OLD PATTERN - DEPRECATED).

## `src/ntag424_sdm_provisioner/commands/get_chip_version.py`
- `class Ntag424VersionInfo` (Line 15)
  > Version information from NTAG424 DNA chip.
    - `def __str__` (Line 36)
- `class GetChipVersion` (Line 60)
  > Retrieves detailed version information from the NTAG424 DNA chip.
  > Returns hardware info, software info, UID, batch number, and fabrication data.
    - `def __init__` (Line 69)
    - `def __str__` (Line 72)
    - `def build_apdu` (Line 75)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 79)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/get_file_counters.py`
- `class GetFileCounters` (Line 17)
  > Retrieves the SDM read counter for a specific file.
  > The SDM read counter increments each time the file is read in unauthenticated
  > mode with SDM enabled. This is used for replay protection in SUN URLs.
  > Command: 90 C1 00 00 01 [FileNo] 00
  > Response: [Counter: 3 bytes, LSB first] 9000
  > Example:
  > >>> cmd = GetFileCounters(file_no=0x02)
  > >>> counter = cmd.execute(connection)
  > >>> print(f"File counter: {counter}")
    - `def __init__` (Line 33)
      > Initialize GetFileCounters command.
    - `def __str__` (Line 43)
    - `def execute` (Line 46)
      > Execute GetFileCounters command.

## `src/ntag424_sdm_provisioner/commands/get_file_ids.py`
- `class GetFileIds` (Line 13)
  > Get list of file IDs in the current application.
  > Returns the list of files available in the selected PICC application.
    - `def __init__` (Line 20)
    - `def __str__` (Line 23)
    - `def build_apdu` (Line 26)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 30)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/get_file_settings.py`
- `class GetFileSettings` (Line 15)
  > Get settings for a specific file.
  > Can be called with regular or authenticated connection.
  > Most files allow reading settings without authentication (CommMode.PLAIN).
    - `def __init__` (Line 23)
    - `def __str__` (Line 27)
    - `def build_apdu` (Line 30)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 34)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/get_key_version.py`
- `class KeyVersionResponse` (Line 15)
  > Response from GetKeyVersion command.
    - `def __str__` (Line 20)
- `class GetKeyVersion` (Line 24)
  > Get version of a specific key.
  > Typically requires authentication (CommMode.MAC), but works with
  > both regular and authenticated connections.
    - `def __init__` (Line 32)
    - `def __str__` (Line 36)
    - `def build_apdu` (Line 39)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 43)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/iso_commands.py`
- `class ISOFileID` (Line 14)
  > ISO 7816 Elementary File IDs for NTAG424 DNA.
    - `def __str__` (Line 20)
- `class ISOSelectFile` (Line 24)
  > ISO 7816-4 SELECT FILE command.
  > Selects an Elementary File (EF) by file identifier for subsequent
  > read/write operations.
    - `def __init__` (Line 39)
      > Args:
    - `def __str__` (Line 48)
    - `def build_apdu` (Line 56)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 72)
      > Parse response for new connection.send(command) pattern.
- `class ISOReadBinary` (Line 81)
  > ISO 7816-4 READ BINARY command.
  > Reads binary data from the currently selected Elementary File.
  > Must call ISOSelectFile first to select the target file.
    - `def __init__` (Line 89)
      > Args:
    - `def __str__` (Line 100)
    - `def build_apdu` (Line 103)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 113)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/read_data.py`
- `class ReadData` (Line 16)
  > Reads data from a standard file on the card.
  > Command: 90 BD 00 00 07 [FileNo] [Offset:3] [Length:3] 00
  > Example:
  > >>> cmd = ReadData(file_no=0x02, offset=0, length=256)
  > >>> response = cmd.execute(connection)
  > >>> print(f"Read {len(response.data)} bytes")
    - `def __init__` (Line 28)
      > Initialize ReadData command.
    - `def __str__` (Line 42)
    - `def execute` (Line 45)
      > Execute ReadData command.

## `src/ntag424_sdm_provisioner/commands/sdm_helpers.py`
- `def calculate_sdm_offsets` (Line 10)
  > Calculate byte offsets for SDM mirrors in NDEF message.
- `def build_sdm_settings_payload` (Line 83)
  > Build the file settings data payload for ChangeFileSettings command.
- `def build_ndef_uri_record` (Line 176)
  > Build NDEF Type 4 Tag message with URI record.
- `def parse_file_settings` (Line 227)
  > Parse GetFileSettings response data into structured format.
- `def parse_key_version` (Line 330)
  > Parse GetKeyVersion response data into structured format.

## `src/ntag424_sdm_provisioner/commands/select_picc_application.py`
- `class SelectPiccApplication` (Line 15)
  > Selects the main PICC-level application on the NTAG424 DNA tag.
  > This must be called before any other NTAG424-specific commands.
  > The PICC application has AID: D2760000850101
    - `def __init__` (Line 25)
    - `def __str__` (Line 28)
    - `def build_apdu` (Line 31)
      > Build APDU for new connection.send(command) pattern.
    - `def parse_response` (Line 35)
      > Parse response for new connection.send(command) pattern.

## `src/ntag424_sdm_provisioner/commands/sun_commands.py`
- `class WriteNdefMessage` (Line 16)
  > Write NDEF message to NTAG424 DNA tag.
  > Uses standard command pattern. HAL automatically handles chunking
  > for large writes via connection.send().
    - `def __init__` (Line 24)
      > Args:
    - `def __str__` (Line 32)
    - `def build_apdu` (Line 35)
      > Build APDU for NDEF write.
    - `def parse_response` (Line 54)
      > Parse response after write completes.
- `class ReadNdefMessage` (Line 59)
  > Read NDEF message from NTAG424 DNA tag.
  > This reads the current NDEF data, which may include SUN-generated
  > dynamic authentication codes if the tag has been scanned.
    - `def __init__` (Line 67)
      > Args:
    - `def __str__` (Line 75)
    - `def execute` (Line 78)
      > Read NDEF message from the tag.
- `class ConfigureSunSettings` (Line 108)
  > Configure SUN (Secure Unique NFC) settings for Seritag tags.
  > SUN settings control how dynamic authentication codes are generated
  > and appended to NDEF messages.
    - `def __init__` (Line 116)
      > Args:
    - `def __str__` (Line 126)
    - `def execute` (Line 129)
      > Configure SUN settings.
- `def build_ndef_uri_record` (Line 174)
  > Build NDEF URI record for SUN authentication.
- `def parse_sun_url` (Line 214)
  > Parse SUN-enhanced URL to extract authentication data.

## `src/ntag424_sdm_provisioner/commands/write_data.py`
- `class WriteData` (Line 16)
  > Writes data to a standard file on the card.
  > Command: 90 3D 00 00 [Lc] [FileNo] [Offset:3] [Length:3] [Data] 00
  > Example:
  > >>> cmd = WriteData(file_no=0x02, offset=0, data_to_write=b'Hello')
  > >>> result = cmd.execute(connection)
    - `def __init__` (Line 27)
      > Initialize WriteData command.
    - `def __str__` (Line 41)
    - `def execute` (Line 44)
      > Execute WriteData command.

## `src/ntag424_sdm_provisioner/commands/write_ndef_message.py`
- `class WriteNdefMessage` (Line 15)
  > Write NDEF message (unauthenticated).
  > HAL automatically chunks large writes via connection.send().
  > Standard UpdateBinary ISO command.
    - `def __init__` (Line 23)
      > Args:
    - `def __str__` (Line 31)
    - `def build_apdu` (Line 34)
      > Build UpdateBinary APDU.
    - `def parse_response` (Line 56)
      > Parse response after write.
- `class WriteNdefMessageAuth` (Line 61)
  > Write NDEF message (authenticated).
  > This uses CommMode.Plain with MAC-only protection. The payload remains
  > unencrypted per NT4H2421Gx Section 10.5 (UpdateBinary), but access rights
  > enforce that the command is accepted only inside a secure messaging session.
    - `def __init__` (Line 70)
    - `def __str__` (Line 74)
    - `def get_command_byte` (Line 77)
      > INS for UpdateBinary.
    - `def get_unencrypted_header` (Line 81)
      > Offset (P1|P2) remains in the clear per spec (offset 0).
    - `def needs_encryption` (Line 85)
      > NDEF file is configured for CommMode.Plain; data remains plaintext but
    - `def build_command_data` (Line 92)
      > Return plaintext NDEF payload (MAC applied by connection).
    - `def parse_response` (Line 96)
      > Return success response after authenticated write.

## `src/ntag424_sdm_provisioner/constants.py`
- `class StatusWord` (Line 11)
  > ISO 7816-4 Status Words.
  > Stored as 16-bit value: (SW1 << 8) | SW2
    - `def from_bytes` (Line 60)
      > Create StatusWord from SW1 and SW2 bytes.
    - `def to_tuple` (Line 69)
      > Convert to (SW1, SW2) tuple.
    - `def is_success` (Line 73)
      > Check if status indicates success.
    - `def is_error` (Line 77)
      > Check if status indicates an error.
    - `def __str__` (Line 81)
- `class StatusWordPair` (Line 85)
  > Status word pairs as Enum for better code readability and debugging.
  > Each value is a (SW1, SW2) tuple that can be compared directly with tuples.
    - `def __eq__` (Line 104)
      > Allow comparison with tuples: if (sw1, sw2) == StatusWordPair.SW_OK
    - `def __hash__` (Line 110)
      > Make hashable for use in sets/dicts
    - `def to_status_word` (Line 114)
      > Convert to StatusWord enum
    - `def __str__` (Line 119)
    - `def __repr__` (Line 123)
- `class APDUClass` (Line 142)
  > APDU Class bytes.
    - `def __str__` (Line 149)
- `class APDUInstruction` (Line 153)
  > APDU Instruction bytes (INS).
    - `def __str__` (Line 194)
- `class FileNo` (Line 202)
  > Standard file numbers on NTAG424 DNA.
    - `def __str__` (Line 208)
- `class KeyNo` (Line 216)
  > Key numbers for authentication.
    - `def __str__` (Line 224)
- `class CommMode` (Line 236)
  > Communication modes for file access.
    - `def __str__` (Line 245)
    - `def requires_auth` (Line 248)
      > Check if this mode requires authentication.
    - `def from_file_option` (Line 253)
      > Extract CommMode from FileOption byte.
- `class FileType` (Line 274)
  > File types on NTAG424 DNA.
    - `def __str__` (Line 282)
- `class AccessRight` (Line 290)
  > Individual access right values (nibble values 0-F).
    - `def __str__` (Line 301)
- `class AccessRights` (Line 306)
  > NTAG424 DNA access rights (2 bytes / 4 nibbles).
  > Byte layout:
  > Byte 1 [7:4]: Read access
  > Byte 1 [3:0]: Write access
  > Byte 0 [7:4]: ReadWrite access
  > Byte 0 [3:0]: Change access (ChangeFileSettings)
    - `def __post_init__` (Line 321)
      > Convert int values to AccessRight enums if needed.
    - `def to_bytes` (Line 328)
      > Convert to NTAG424 2-byte format.
    - `def from_bytes` (Line 335)
      > Parse from 2-byte format.
    - `def __str__` (Line 349)
- `class AccessRightsPresets` (Line 362)
  > Common access rights configurations.
- `class SDMOption` (Line 398)
  > SDM configuration options (bit flags).
  > Can be combined using bitwise OR: SDMOption.ENABLED | SDMOption.UID_MIRROR
- `class NdefUriPrefix` (Line 419)
  > NDEF URI identifier codes.
    - `def __str__` (Line 433)
    - `def to_prefix_string` (Line 436)
      > Convert prefix code to actual URL prefix string.
- `class NdefRecordType` (Line 454)
  > NDEF Record Type Name Format (TNF).
    - `def __str__` (Line 465)
- `class NdefTLV` (Line 469)
  > NDEF TLV types for Type 4 Tags.
    - `def __str__` (Line 478)
- `class MemorySize` (Line 486)
  > Standard memory sizes for NTAG424 DNA variants.
- `class ApplicationID` (Line 496)
  > Application IDs for NTAG424 DNA.
- `class ErrorCategory` (Line 505)
  > Categories of errors for better error handling.
    - `def __str__` (Line 516)
- `def get_error_category` (Line 549)
  > Get error category for a status word.
- `class SuccessResponse` (Line 559)
  > Response for successful operations.
    - `def __str__` (Line 563)
- `class AuthenticationChallengeResponse` (Line 568)
  > Response from EV2 authentication first phase.
    - `def __str__` (Line 573)
- `class AuthenticationResponse` (Line 578)
  > Response from EV2 authentication second phase.
    - `def __str__` (Line 585)
- `class Ntag424VersionInfo` (Line 593)
  > Version information from NTAG424 DNA chip.
    - `def __str__` (Line 614)
- `class ReadDataResponse` (Line 639)
  > Response from file read operations.
    - `def __str__` (Line 647)
- `class FileOption` (Line 655)
  > File option flags for SDM configuration.
  > Note: These combine FileOption byte (bits 1-0 = CommMode, bit 6 = SDM enable)
  > with SDMOptions byte (bits for UID/counter mirroring).
  > FileOption byte:
  > - Bit 6: SDM enabled (0x40)
  > - Bits 1-0: CommMode
  > SDMOptions byte:
  > - Bit 7: UID mirror (0x80)
  > - Bit 6: Read counter (0x40)
  > - Bit 5: Counter limit (0x20)
  > - Bit 4: Encrypt file data (0x10)
- `class FileSettingsResponse` (Line 680)
  > Response from GetFileSettings command.
    - `def get_comm_mode` (Line 698)
      > Get the communication mode for this file.
    - `def requires_authentication` (Line 709)
      > Check if this file requires authentication for access.
    - `def __str__` (Line 718)
- `class KeyVersionResponse` (Line 790)
  > Response from GetKeyVersion command.
    - `def __str__` (Line 795)
- `class SDMOffsets` (Line 804)
  > SDM offset configuration with sane defaults.
    - `def __str__` (Line 813)
- `class SDMConfiguration` (Line 825)
  > Configuration for Secure Dynamic Messaging.
    - `def __post_init__` (Line 834)
      > Validate and normalize configuration.
    - `def get_access_rights_bytes` (Line 854)
      > Get access rights as bytes (internal encoding).
- `class SDMUrlTemplate` (Line 860)
  > Template for building SDM-enabled URLs.
  > Contains the base URL and placeholders for SDM parameters.
    - `def generate_url` (Line 872)
      > Generate a complete URL with provided values.
- `class AuthSessionKeys` (Line 900)
  > Session keys derived from EV2 authentication.
- `def describe_status_word` (Line 913)
  > Get human-readable description of status word.
- `class CCFileData` (Line 945)
  > Capability Container file data for NFC Type 4 Tag.
  > The CC file tells phones/readers where to find NDEF data and
  > what access conditions apply.
    - `def from_bytes` (Line 980)
      > Parse CC file data from raw bytes.
    - `def to_bytes` (Line 1032)
      > Convert CC file data to raw bytes.

## `src/ntag424_sdm_provisioner/crypto/aes.py`
- `class AesKey` (Line 4)
  > Wrapper for AES-128 key operations.
    - `def __init__` (Line 8)
    - `def encrypt` (Line 13)
      > Encrypt data using AES-CBC.
    - `def decrypt` (Line 20)
      > Decrypt data using AES-CBC.
    - `def cmac` (Line 27)
      > Calculate CMAC.
    - `def __bytes__` (Line 33)

## `src/ntag424_sdm_provisioner/crypto/auth_session.py`
- `class Ntag424AuthSession` (Line 28)
  > Handles EV2 authentication and session key management for NTAG424 DNA.
  > Manages the two-phase authentication protocol and derives session keys
  > for subsequent encrypted/MACed commands.
    - `def __init__` (Line 36)
      > Initialize authentication session.
    - `def authenticate` (Line 53)
      > Perform complete EV2 authentication (both phases).
    - `def _phase1_get_challenge` (Line 92)
      > Phase 1: Send authentication request and get encrypted RndB.
    - `def _phase2_authenticate` (Line 127)
      > Phase 2: Decrypt RndB, generate RndA, authenticate, derive keys.
    - `def _decrypt_rndb` (Line 181)
      > Decrypt RndB received from card using verified crypto_primitives.
    - `def _encrypt_response` (Line 195)
      > Encrypt authentication response (RndA + RndB') using verified crypto_primitives.
    - `def _parse_card_response` (Line 210)
      > Parse and decrypt the card's authentication response.
    - `def _derive_session_keys` (Line 252)
      > Derive session encryption and MAC keys from RndA, RndB, and Ti.
    - `def apply_cmac` (Line 285)
      > Apply CMAC to command data for authenticated commands.
    - `def encrypt_data` (Line 338)
      > Encrypt data using session encryption key.
    - `def decrypt_data` (Line 374)
      > Decrypt data using session encryption key.
    - `def _derive_iv` (Line 409)
      > Derive IV for encryption/decryption using verified crypto_primitives.
    - `def _iso7816_4_pad` (Line 427)
      > Apply ISO/IEC 9797-1 Padding Method 2 (ISO 7816-4).
    - `def _iso7816_4_unpad` (Line 456)
      > Remove ISO/IEC 9797-1 Padding Method 2 (ISO 7816-4).
    - `def _pkcs7_pad` (Line 481)
      > Apply PKCS7 padding to data.
    - `def _pkcs7_unpad` (Line 499)
      > Remove PKCS7 padding from data.

## `src/ntag424_sdm_provisioner/crypto/crypto_primitives.py`
- `def calculate_iv_for_command` (Line 16)
  > Calculate IV for command encryption per NXP spec.
- `def encrypt_key_data` (Line 49)
  > Encrypt key data using AES-CBC.
- `def calculate_cmac_full` (Line 74)
  > Calculate full 16-byte CMAC.
- `def truncate_cmac` (Line 93)
  > Truncate CMAC to 8 bytes using even-numbered bytes (odd indices).
- `def calculate_cmac` (Line 119)
  > Calculate truncated CMAC for authenticated command.
- `def build_key_data` (Line 155)
  > Build 32-byte key data for ChangeKey command.
- `def decrypt_rndb` (Line 211)
  > Decrypt RndB from authentication Phase 1 response.
- `def rotate_left` (Line 233)
  > Rotate bytes left by 1 byte.
- `def encrypt_auth_response` (Line 252)
  > Encrypt authentication Phase 2 response.
- `def decrypt_auth_response` (Line 276)
  > Decrypt authentication Phase 2 card response.
- `def derive_session_keys` (Line 297)
  > Derive session encryption and MAC keys from RndA, RndB.
- `def build_changekey_apdu` (Line 350)
  > Build complete ChangeKey APDU with encryption and CMAC.

## `src/ntag424_sdm_provisioner/csv_key_manager.py`
- `class TagKeys` (Line 21)
  > Keys and metadata for a single NTAG424 DNA tag.
    - `def get_picc_master_key_bytes` (Line 31)
      > Get PICC master key as bytes.
    - `def get_app_read_key_bytes` (Line 35)
      > Get app read key as bytes.
    - `def get_sdm_mac_key_bytes` (Line 39)
      > Get SDM MAC key as bytes.
    - `def get_asset_tag` (Line 43)
      > Get short asset tag code from UID.
    - `def __str__` (Line 48)
      > Format TagKeys for display.
    - `def from_factory_keys` (Line 62)
      > Create TagKeys entry with factory default keys.
- `class BackupEntry` (Line 77)
  > Represents a backup snapshot for a tag.
- `class CsvKeyManager` (Line 84)
  > CSV-based key manager implementing the KeyManager protocol.
  > Keys are stored in a primary CSV file (tag_keys.csv) and backed up
  > to a backup file (tag_keys_backup.csv) before any changes.
  > This provides:
  > - Persistent storage of unique keys per tag
  > - Automatic backup before key changes
  > - Factory key fallback for new tags
  > - Compatible with KeyManager protocol
    - `def __init__` (Line 101)
      > Initialize key manager.
    - `def _ensure_csv_exists` (Line 113)
      > Create CSV file with headers if it doesn't exist.
    - `def get_key` (Line 127)
      > Get key for a specific tag and key number (implements KeyManager protocol).
    - `def get_tag_keys` (Line 157)
      > Get all keys for a specific tag UID.
    - `def save_tag_keys` (Line 181)
      > Save or update all keys for a tag.
    - `def backup_keys` (Line 227)
      > Backup keys to backup file with timestamp.
    - `def _load_backups_for_uid` (Line 248)
      > Load all backup entries for the given UID (newest first).
    - `def get_backup_entries` (Line 276)
      > Return backup entries for the UID, sorted newest first.
    - `def restore_from_backup` (Line 280)
      > Restore the most recent backup entry for the UID back into the main CSV.
    - `def list_tags` (Line 300)
      > List all tags in the database.
    - `def generate_random_keys` (Line 316)
      > Generate random keys for a tag.
    - `def provision_tag` (Line 341)
      > Context manager for two-phase commit of tag provisioning.
    - `def print_summary` (Line 411)
      > Print summary of all tags in database.

## `src/ntag424_sdm_provisioner/hal.py`
- `def hexb` (Line 22)
  > Format bytes or list of ints as hex string (no smartcard dependency).
- `def format_status_word` (Line 31)
  > Format status word with enum name for readability.
- `class NTag242ConnectionError` (Line 43)
  > Custom exception for connection failures.
- `class NTag242NoReadersError` (Line 47)
  > Custom exception for when no readers are found.
- `class ApduError` (Line 51)
  > Custom exception for APDU command failures.
- `class CardManager` (Line 55)
  > A robust context manager that uses a direct, blocking call to wait for a
  > card tap, then establishes a clean connection.
    - `def __init__` (Line 60)
    - `def __enter__` (Line 66)
    - `def __exit__` (Line 120)
- `class NTag424CardConnection` (Line 131)
  > A wrapper for a pyscard CardConnection that handles the low-level
  > details of APDU transmission.
    - `def __init__` (Line 136)
    - `def __str__` (Line 139)
    - `def wait_for_atr` (Line 142)
    - `def check_response` (Line 145)
      > Check response status word and raise ApduError if not expected.
    - `def send` (Line 169)
      > Send a command to the card (NEW PATTERN).
    - `def _needs_chunking` (Line 210)
      > Check if APDU needs chunking (UpdateBinary with large data).
    - `def _send_chunked_write` (Line 225)
      > Send large write in chunks using existing send_write_chunked().
    - `def send_write_chunked` (Line 245)
      > Send write command with automatic chunking for large data.
    - `def send_apdu` (Line 303)
      > Sends a raw APDU command to the card and returns the response.
- `class _AtrObserver` (Line 351)
    - `def __init__` (Line 352)
    - `def update` (Line 358)
    - `def wait_for_next_atr` (Line 393)
- `def watch_atrs` (Line 404)
- `def wait_for_card_atr` (Line 418)
  > Block until the next card is presented (or timeout) and return ATR bytes.

## `src/ntag424_sdm_provisioner/key_manager.py`
- `class KeyManager` (Line 26)
  > Legacy-compatible KeyManager interface.
  > Implementations should return a 16-byte AES key for a given tag UID and
  > key number.
    - `def get_key_for_uid` (Line 34)
- `class KeyGenerator` (Line 38)
  > Generates or derives keys and supports optional wrapping.
  > Implementations MUST NOT log or expose key material.
    - `def derive_key` (Line 45)
      > Deterministically derive a 16-byte key for a UID and key number.
    - `def wrap_key` (Line 49)
      > Wraps (encrypts) a key with a Key-Encryption-Key. Returns wrapped blob.
    - `def unwrap_key` (Line 53)
      > Unwraps (decrypts) a wrapped key with a Key-Encryption-Key.
- `class KeyStorage` (Line 57)
  > Abstract key storage backend.
  > Storage backends decide whether keys are stored plaintext or wrapped.
    - `def get_key` (Line 64)
    - `def store_key` (Line 68)
    - `def delete_key` (Line 72)
- `class DerivingKeyGenerator` (Line 76)
  > Derives per-UID keys using AES-CMAC (deterministic) and provides a
  > simple AES-CBC based wrapper for examples/tests.
  > Notes:
  > - Derivation: SesKey = CMAC(master_key, uid || key_no_byte)
  > - Wrapping: AES-CBC with random IV prefixed (not RFC3394). This is
  > sufficient for demonstration and tests but not recommended for HSM-grade
  > key transport.
    - `def __init__` (Line 87)
    - `def derive_key` (Line 92)
    - `def wrap_key` (Line 101)
    - `def unwrap_key` (Line 112)
- `class InMemoryKeyStorage` (Line 125)
  > A simple volatile storage used for tests and examples.
    - `def __init__` (Line 128)
    - `def _k` (Line 132)
    - `def get_key` (Line 135)
    - `def store_key` (Line 138)
    - `def delete_key` (Line 141)
- `class DerivedKeyManager` (Line 145)
  > High-level KeyManager that composes a KeyGenerator and KeyStorage.
  > Behavior:
  > - When `get_key_for_uid` is called, storage is consulted first.
  > - If not present, the generator derives the key, it is stored, and returned.
    - `def __init__` (Line 153)
    - `def get_key_for_uid` (Line 157)
- `class StaticKeyManager` (Line 166)
  > Backwards-compatible static key manager (keeps previous behavior).
  > Internally uses InMemoryKeyStorage to satisfy the KeyManager API.
    - `def __init__` (Line 172)
    - `def get_key_for_uid` (Line 182)

## `src/ntag424_sdm_provisioner/key_manager_interface.py`
- `class KeyManager` (Line 18)
  > Protocol (interface) for key management.
  > This defines the contract that any key manager implementation must follow.
  > Implementations can use factory keys, derived keys, or retrieve from database.
    - `def get_key` (Line 26)
      > Retrieve the key for a specific tag and key number.
- `class SimpleKeyManager` (Line 46)
  > Simple key manager that uses factory default keys for all tags.
  > This is a temporary implementation for initial development and testing.
  > It does NOT provide unique keys per coin - all coins use the same keys.
  > Use this during development. Replace with UniqueKeyManager later for production.
    - `def __init__` (Line 56)
      > Initialize with factory key.
    - `def get_key` (Line 67)
      > Returns the factory key for all UIDs and key numbers.
    - `def __str__` (Line 85)
- `class UniqueKeyManager` (Line 90)
  > FUTURE: Key manager that derives unique keys per coin.
  > This will implement CMAC-based key derivation function (KDF) to generate
  > unique keys for each coin based on:
  > - Master key (secret, stored securely)
  > - Tag UID (unique per coin)
  > - Key number (0-4)
  > Algorithm (from NXP AN12196):
  > derived_key = CMAC(master_key, 0x01 || UID || key_no)
  > Benefits:
  > - Each coin has unique keys
  > - Compromising one coin doesn't affect others
  > - Keys can be regenerated from UID (no database needed)
    - `def __init__` (Line 109)
      > Initialize with master key.
    - `def get_key` (Line 121)
      > Derives unique key for UID + key_no using CMAC-KDF.
- `def create_key_manager` (Line 127)
  > Factory function to create appropriate key manager.

## `src/ntag424_sdm_provisioner/seritag_simulator.py`
- `class SeritagTagState` (Line 17)
  > State of the simulated Seritag NTAG424 DNA tag.
    - `def __post_init__` (Line 52)
- `class SeritagSimulator` (Line 62)
  > Simulates a Seritag NTAG424 DNA tag.
    - `def __init__` (Line 65)
    - `def connect` (Line 69)
      > Simulate card connection.
    - `def disconnect` (Line 74)
      > Simulate card disconnection.
    - `def send_apdu` (Line 80)
      > Simulate APDU command processing.
    - `def _handle_select_application` (Line 127)
      > Handle Select PICC Application command.
    - `def _handle_get_version` (Line 132)
      > Handle Get Chip Version command according to NTAG424 DNA specification.
    - `def _handle_authenticate_ev2_first` (Line 195)
      > Handle AuthenticateEV2First command with proper EV2 implementation.
    - `def _handle_authenticate_ev2_second` (Line 225)
      > Handle AuthenticateEV2Second command with proper EV2 implementation.
    - `def _handle_select_file` (Line 283)
      > Handle Select File command.
    - `def _handle_update_binary` (Line 300)
      > Handle Update Binary command.
    - `def _handle_change_file_settings` (Line 322)
      > Handle ChangeFileSettings command.
- `class SeritagCardConnection` (Line 339)
  > Simulated Seritag card connection.
    - `def __init__` (Line 342)
    - `def send_apdu` (Line 345)
      > Send APDU to simulated Seritag tag.
    - `def send` (Line 350)
      > Support for high-level Command objects (like NTag424CardConnection.send).
    - `def transmit` (Line 371)
      > Alias for send_apdu to match pyscard interface.
    - `def control` (Line 375)
      > Simulate control command (for escape sequences).
- `class SeritagCardManager` (Line 382)
  > Simulated card manager for Seritag tags.
    - `def __init__` (Line 385)
    - `def __enter__` (Line 390)
      > Context manager entry.
    - `def __exit__` (Line 398)
      > Context manager exit.

## `src/ntag424_sdm_provisioner/services/provisioning_service.py`
- `class ProvisioningService` (Line 24)
  > Core business logic for provisioning NTAG424 DNA tags.
  > UI-agnostic: uses callbacks for progress updates.
    - `def __init__` (Line 29)
    - `def _log` (Line 34)
    - `def provision` (Line 39)
      > Execute complete provisioning workflow.
    - `def _determine_current_keys` (Line 106)
    - `def _authenticate` (Line 121)
    - `def _configure_sdm` (Line 130)
    - `def _write_ndef` (Line 152)

## `src/ntag424_sdm_provisioner/tools/base.py`
- `class TagState` (Line 15)
  > Current state of a tag.
  > Assessed by runner before offering tools to user.
  > Passed to tools for decision making.
- `class ConfirmationRequest` (Line 30)
  > Request for user confirmation before executing tool.
  > Runner displays this and gets user input before calling tool.execute().
- `class ToolResult` (Line 42)
  > Result from tool execution.
  > Tools return this instead of printing. Runner handles display.
- `class Tool` (Line 53)
  > Protocol for tag tools.
  > Tools are pure business logic - no I/O!
  > Runner handles all display and input.
    - `def is_available` (Line 63)
      > Check if tool can run on this tag.
    - `def get_confirmation_request` (Line 73)
      > Get confirmation details if tool needs user approval.
    - `def execute` (Line 83)
      > Execute tool logic - NO I/O!

## `src/ntag424_sdm_provisioner/tools/configure_sdm_tool.py`
- `class ConfigureSdmTool` (Line 21)
  > Configure Secure Dynamic Messaging on a provisioned tag.
  > Authenticates with PICC Master Key and configures SDM with:
  > - UID mirroring
  > - Read counter
  > - CMAC for authentication
    - `def __init__` (Line 34)
    - `def is_available` (Line 37)
      > SDM config requires tag to be provisioned with known keys.
    - `def get_confirmation_request` (Line 45)
      > Request confirmation before configuring SDM.
    - `def execute` (Line 60)
      > Configure SDM - pure business logic, no I/O.

## `src/ntag424_sdm_provisioner/tools/diagnostics_tool.py`
- `class DiagnosticsTool` (Line 17)
  > Collect complete tag diagnostics.
  > Read-only tool that gathers all tag information for troubleshooting.
    - `def is_available` (Line 27)
      > Always available.
    - `def get_confirmation_request` (Line 31)
      > No confirmation needed for read-only diagnostics.
    - `def execute` (Line 35)
      > Collect all diagnostic information - no I/O!

## `src/ntag424_sdm_provisioner/tools/provision_factory_tool.py`
- `class ProvisionFactoryTool` (Line 21)
  > Initial provisioning of factory-default tags.
    - `def __init__` (Line 27)
    - `def is_available` (Line 30)
      > Available only for factory/unknown tags.
    - `def get_confirmation_request` (Line 36)
      > Confirm full provisioning.
    - `def execute` (Line 51)
      > Provision factory tag with random keys and SDM.

## `src/ntag424_sdm_provisioner/tools/read_url_tool.py`
- `class ReadUrlTool` (Line 11)
  > Display current NDEF URL without modifying tag.
    - `def is_available` (Line 17)
      > Always available if tag has NDEF.
    - `def get_confirmation_request` (Line 23)
      > No confirmation needed for read-only operation.
    - `def execute` (Line 27)
      > Read and return current URL.
    - `def _extract_url_from_ndef` (Line 48)
      > Extract URL string from NDEF data.

## `src/ntag424_sdm_provisioner/tools/reprovision_tool.py`
- `class ReprovisionTool` (Line 14)
  > Change all keys on a provisioned tag.
    - `def is_available` (Line 20)
      > Available if tag is provisioned with known keys.
    - `def get_confirmation_request` (Line 28)
      > Confirm key change.
    - `def execute` (Line 42)
      > Change all keys to new random values.

## `src/ntag424_sdm_provisioner/tools/restore_backup_tool.py`
- `class RestoreBackupTool` (Line 15)
  > Restore keys from backup when database is corrupted.
    - `def is_available` (Line 22)
      > Available if tag has backups.
    - `def get_confirmation_request` (Line 28)
      > Confirm restoration.
    - `def execute` (Line 40)
      > Iterate through backup snapshots until authentication succeeds.

## `src/ntag424_sdm_provisioner/tools/runner.py`
- `class ToolRunner` (Line 27)
  > Main orchestrator for tool-based tag operations.
  > Manages:
  > - Tag connection/disconnection per operation
  > - Tag state assessment
  > - Tool filtering based on preconditions
  > - Menu display and user interaction
  > - Tool execution with error handling
    - `def __init__` (Line 39)
      > Initialize tool runner.
    - `def _connect_to_tag` (Line 54)
      > Connect to tag on reader, yield connection, disconnect.
    - `def _get_tag_state_fresh` (Line 73)
      > Assess tag state using a fresh connection.
    - `def _collect_diagnostics` (Line 83)
      > Run diagnostics tool with a fresh connection and return details.
    - `def _execute_tool_auto` (Line 96)
      > Execute a tool using a fresh connection (no prompts/prints).
    - `def run_auto` (Line 122)
      > Perform automatic SDM provisioning workflow.
    - `def _assess_tag_state` (Line 254)
      > Assess current state of the tag.
    - `def _get_backups_for_uid` (Line 306)
      > Load all backups for a specific UID.
    - `def _show_menu` (Line 328)
      > Display menu showing ALL tools (available and unavailable).
    - `def _display_result_details` (Line 409)
      > Display tool result details with custom formatting per tool.
    - `def _display_diagnostics` (Line 430)
      > Display diagnostics with structured formatting.
    - `def _run_tool` (Line 501)
      > Run a tool with centralized I/O handling.
    - `def run` (Line 561)
      > Main loop: connect → assess → menu → execute → repeat.

## `src/ntag424_sdm_provisioner/tools/tool_helpers.py`
- `def read_ndef_file` (Line 20)
  > Read entire NDEF file from tag.
- `def has_ndef_content` (Line 44)
  > Check if NDEF data contains meaningful content.
- `def extract_url_from_ndef` (Line 65)
  > Extract URL from NDEF data.
- `def format_url_for_display` (Line 112)
  > Format URL for display with truncation if needed.
- `def build_sdm_url_template` (Line 133)
  > Build SDM URL template with standard placeholders.
- `def configure_sdm_with_offsets` (Line 152)
  > Configure SDM file settings using authenticated ChangeFileSettings.

## `src/ntag424_sdm_provisioner/tools/update_url_tool.py`
- `class UpdateUrlTool` (Line 15)
  > Change NDEF URL without modifying cryptographic keys.
    - `def __init__` (Line 21)
    - `def is_available` (Line 24)
      > Available if tag has NDEF content.
    - `def get_confirmation_request` (Line 30)
      > Request new URL from user.
    - `def execute` (Line 42)
      > Update URL - business logic only.
    - `def _extract_url` (Line 70)
      > Extract URL from NDEF data.

## `src/ntag424_sdm_provisioner/trace_util.py`
- `def trace_calls` (Line 26)
  > Decorator to trace function calls with arguments and return values.
- `def trace_block` (Line 64)
  > Context manager to trace a block of code.
- `def _format_value` (Line 85)
  > Format a value for logging, with special handling for bytes.
- `def trace_apdu` (Line 110)
  > Log an APDU with nice formatting.
- `def trace_crypto` (Line 146)
  > Log cryptographic operation details.
- `def enable_trace_logging` (Line 162)
  > Enable TRACE level logging for all trace utilities.
- `def disable_trace_logging` (Line 167)
  > Disable TRACE level logging.

## `src/ntag424_sdm_provisioner/tui/app.py`
- `class NtagProvisionerApp` (Line 12)
  > A Textual app for NTAG424 DNA Provisioning.
    - `def on_mount` (Line 53)
    - `def action_switch_mode` (Line 59)

## `src/ntag424_sdm_provisioner/tui/clock.py`
- `class Clock` (Line 8)
  > Abstract clock for time-dependent operations.
    - `def sleep` (Line 12)
      > Sleep for specified duration.
    - `def schedule` (Line 17)
      > Schedule callback after delay.
- `class RealClock` (Line 22)
  > Production clock using real time.
    - `def sleep` (Line 25)
    - `def schedule` (Line 28)
- `class FakeClock` (Line 33)
  > Test clock with manual time control for deterministic testing.
    - `def __init__` (Line 36)
    - `def sleep` (Line 40)
    - `def advance` (Line 43)
      > Manually advance time (for tests).
    - `def schedule` (Line 48)
    - `def _run_scheduled` (Line 53)
      > Run all callbacks whose time has come.
    - `def current_time` (Line 60)
      > Get current (fake) time.

## `src/ntag424_sdm_provisioner/tui/commands/provision_tag_command.py`
- `class ProvisionTagCommand` (Line 9)
  > Provision tag without UI dependency.
    - `def __init__` (Line 12)
    - `def timeout_seconds` (Line 21)
    - `def operation_name` (Line 25)
    - `def execute` (Line 28)
      > Execute the provision operation.

## `src/ntag424_sdm_provisioner/tui/commands/read_tag_command.py`
- `class ReadTagCommand` (Line 9)
  > Read tag info without UI dependency.
    - `def __init__` (Line 12)
    - `def timeout_seconds` (Line 16)
    - `def operation_name` (Line 20)
    - `def execute` (Line 23)
      > Execute the read tag operation.

## `src/ntag424_sdm_provisioner/tui/logging_handler.py`
- `class TextualLogHandler` (Line 4)
  > A logging handler that writes to a Textual RichLog widget.
    - `def __init__` (Line 7)
    - `def emit` (Line 12)

## `src/ntag424_sdm_provisioner/tui/nfc_command.py`
- `class NFCCommand` (Line 6)
  > Abstract base for NFC operations.
  > UI-agnostic design allows commands to run:
  > - In TUI (via WorkerManager)
  > - In CLI (headless mode)
  > - In tests (direct call)
    - `def execute` (Line 17)
      > Execute the blocking NFC operation.
    - `def timeout_seconds` (Line 28)
      > Get the operation timeout in seconds.
    - `def operation_name` (Line 34)
      > Get the human-readable operation name (for logging/UI).
    - `def execute_with_progress` (Line 38)
      > Execute with optional progress updates.

## `src/ntag424_sdm_provisioner/tui/screens/main_menu.py`
- `class MainMenu` (Line 5)
  > The main menu screen.
    - `def compose` (Line 8)
    - `def on_button_pressed` (Line 21)

## `src/ntag424_sdm_provisioner/tui/screens/provision.py`
- `class ServiceAdapter` (Line 14)
  > Adapts ProvisioningService to WorkerManager protocol.
    - `def __init__` (Line 16)
    - `def timeout_seconds` (Line 21)
    - `def execute` (Line 24)
      > Execute provisioning via service.
    - `def start_provisioning` (Line 41)
    - `def on_worker_state_changed` (Line 57)

## `src/ntag424_sdm_provisioner/tui/screens/read_tag.py`
- `class ReadTagScreen` (Line 13)
  > Screen for reading tag details.
    - `def compose` (Line 16)
    - `def on_mount` (Line 27)
    - `def on_unmount` (Line 40)
    - `def on_button_pressed` (Line 44)
    - `def scan_tag` (Line 50)
    - `def on_worker_state_changed` (Line 62)

## `src/ntag424_sdm_provisioner/tui/state_manager.py`
- `class StateManager` (Line 1)
  > Manages the state transitions of the TUI application.
    - `def __init__` (Line 5)
    - `def transition_to` (Line 8)
      > Transition to a new state.

## `src/ntag424_sdm_provisioner/tui/tui_main.py`
- `def main` (Line 3)

## `src/ntag424_sdm_provisioner/tui/worker_manager.py`
- `class WorkerManager` (Line 9)
  > Centralized worker orchestration with built-in timer and state management.
  > Eliminates race conditions by encapsulating all async interaction.
    - `def __init__` (Line 15)
    - `def execute_command` (Line 21)
      > Execute NFC command with automatic timer/state management.
    - `def _tick` (Line 48)
      > Timer tick handler (race-safe).
    - `def _update_label` (Line 61)
      > Safely update a label widget.
    - `def cleanup` (Line 70)
      > Cleanup resources (call from on_worker_state_changed).

## `src/ntag424_sdm_provisioner/uid_utils.py`
- `def uid_to_asset_tag` (Line 6)
  > Convert UID to a short asset tag code for labeling.
- `def uid_to_short_hex` (Line 31)
  > Convert UID to compact hex string (last 3 bytes, 6 chars).
- `def asset_tag_matches_uid` (Line 52)
  > Check if an asset tag code matches a UID.
- `def format_uid_with_asset_tag` (Line 79)
  > Format UID with asset tag for display.
- `def get_uid_string` (Line 98)
  > Convert UID bytes to a hex string.