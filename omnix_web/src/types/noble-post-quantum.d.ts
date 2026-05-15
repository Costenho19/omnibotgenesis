declare module '@noble/post-quantum/ml-dsa.js' {
  type BytesOrHex = Uint8Array | string

  interface MLDSASigner {
    sign(secretKey: BytesOrHex, msg: BytesOrHex): Uint8Array
    verify(sig: BytesOrHex, msg: BytesOrHex, publicKey: BytesOrHex): boolean
    generateKeyPair(): { secretKey: Uint8Array; publicKey: Uint8Array }
    keygen(): { secretKey: Uint8Array; publicKey: Uint8Array }
  }

  export const ml_dsa44: MLDSASigner
  export const ml_dsa65: MLDSASigner
  export const ml_dsa87: MLDSASigner
}
