import { create } from 'zustand'
import { invoke } from '@tauri-apps/api/core'

export interface Credential {
  id: number
  domain: string
  username: string
  password: string
  notes?: string
  totp_secret?: string
  backup_codes?: string
  folder_id?: number
  favorite: boolean
  created_at: string
  updated_at: string
}

export interface SecureNote {
  id: number
  title: string
  content: string
  folder_id?: number
  favorite: boolean
  created_at: string
  updated_at: string
}

export interface CreditCard {
  id: number
  title: string
  card_number: string
  cardholder_name: string
  expiry_date: string
  cvv: string
  notes?: string
  favorite: boolean
  folder_id?: number
  created_at: string
  updated_at: string
}

export interface Folder {
  id: number
  name: string
  vault_type: string
  created_at: string
}

interface VaultState {
  credentials: Credential[]
  secureNotes: SecureNote[]
  creditCards: CreditCard[]
  folders: Folder[]
  selectedItem: Credential | SecureNote | CreditCard | null
  selectedCategory: string
  searchQuery: string
  isLoading: boolean
  
  // Actions
  loadVaultData: () => Promise<{ credentials: Credential[]; secureNotes: SecureNote[]; creditCards: CreditCard[]; folders: Folder[]; isLoading: boolean; }>
  setSelectedItem: (item: Credential | SecureNote | CreditCard | null) => void
  setSelectedCategory: (category: string) => void
  setSearchQuery: (query: string) => void
  addCredential: (data: Partial<Credential>) => Promise<void>
  updateCredential: (id: number, data: Partial<Credential>) => Promise<void>
  deleteCredential: (id: number) => Promise<void>
  addSecureNote: (data: Partial<SecureNote>) => Promise<void>
  updateSecureNote: (id: number, data: Partial<SecureNote>) => Promise<void>
  deleteSecureNote: (id: number) => Promise<void>
  addCreditCard: (data: Partial<CreditCard>) => Promise<void>
  updateCreditCard: (id: number, data: Partial<CreditCard>) => Promise<void>
  deleteCreditCard: (id: number) => Promise<void>
  addFolder: (name: string, vaultType?: string) => Promise<void>
  updateFolder: (id: number, name: string) => Promise<void>
  deleteFolder: (id: number) => Promise<void>
}

export const useVaultStore = create<VaultState>((set, get) => ({
  credentials: [],
  secureNotes: [],
  creditCards: [],
  folders: [],
  selectedItem: null,
  selectedCategory: 'all',
  searchQuery: '',
  isLoading: false,

  loadVaultData: async () => {
    set({ isLoading: true })
    try {
      console.log('DEBUG: Loading vault data...')
      const [credsRes, notesRes, cardsRes, foldersRes] = await Promise.all([
        invoke<{ success: boolean; data?: Credential[] }>('get_credentials'),
        invoke<{ success: boolean; data?: SecureNote[] }>('get_secure_notes'),
        invoke<{ success: boolean; data?: CreditCard[] }>('get_credit_cards'),
        invoke<{ success: boolean; data?: Folder[] }>('get_folders'),
      ])

      console.log('DEBUG: Credentials response:', credsRes)
      console.log('DEBUG: Notes response:', notesRes)
      console.log('DEBUG: Cards response:', cardsRes)
      console.log('DEBUG: Folders response:', foldersRes)

      const newState = {
        credentials: credsRes.data || [],
        secureNotes: notesRes.data || [],
        creditCards: cardsRes.data || [],
        folders: foldersRes.data || [],
        isLoading: false,
      }

      set(newState)
      return newState
    } catch (error) {
      console.error('Failed to load vault data:', error)
      set({ isLoading: false })
      throw error
    }
  },

  setSelectedItem: (item) => set({ selectedItem: item }),
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  setSearchQuery: (query) => set({ searchQuery: query }),

  addCredential: async (data) => {
    try {
      const response = await invoke<{ success: boolean; data?: Credential }>(
        'add_credential',
        data
      )
      if (response.success && response.data) {
        set((state) => ({
          credentials: [...state.credentials, response.data!],
        }))
      }
    } catch (error) {
      console.error('Failed to add credential:', error)
    }
  },

  updateCredential: async (id, data) => {
    try {
      await invoke('update_credential', { id, ...data })
      const newState = await get().loadVaultData()
      // Update selectedItem if it's the same credential
      const updatedCredential = newState.credentials.find((c) => c.id === id)
      if (updatedCredential && get().selectedItem && 'domain' in get().selectedItem && get().selectedItem.id === id) {
        set({ selectedItem: updatedCredential })
      }
    } catch (error) {
      console.error('Failed to update credential:', error)
    }
  },

  deleteCredential: async (id) => {
    try {
      await invoke('delete_credential', { id })
      set((state) => ({
        credentials: state.credentials.filter((c) => c.id !== id),
        selectedItem:
          state.selectedItem && 'domain' in state.selectedItem && state.selectedItem.id === id
            ? null
            : state.selectedItem,
      }))
    } catch (error) {
      console.error('Failed to delete credential:', error)
    }
  },

  addSecureNote: async (data) => {
    try {
      const response = await invoke<{ success: boolean; data?: SecureNote }>(
        'add_secure_note',
        data
      )
      if (response.success && response.data) {
        set((state) => ({
          secureNotes: [...state.secureNotes, response.data!],
        }))
      }
    } catch (error) {
      console.error('Failed to add secure note:', error)
    }
  },

  updateSecureNote: async (id, data) => {
    try {
      await invoke('update_secure_note', { id, ...data })
      const newState = await get().loadVaultData()
      // Update selectedItem if it's the same note
      const updatedNote = newState.secureNotes.find((n) => n.id === id)
      if (updatedNote && get().selectedItem && 'content' in get().selectedItem && get().selectedItem.id === id) {
        set({ selectedItem: updatedNote })
      }
    } catch (error) {
      console.error('Failed to update secure note:', error)
    }
  },

  deleteSecureNote: async (id) => {
    try {
      await invoke('delete_secure_note', { id })
      set((state) => ({
        secureNotes: state.secureNotes.filter((n) => n.id !== id),
        selectedItem:
          state.selectedItem && 'title' in state.selectedItem && state.selectedItem.id === id
            ? null
            : state.selectedItem,
      }))
    } catch (error) {
      console.error('Failed to delete secure note:', error)
    }
  },

  addCreditCard: async (data) => {
    try {
      const response = await invoke<{ success: boolean; data?: CreditCard }>(
        'add_credit_card',
        data
      )
      if (response.success && response.data) {
        set((state) => ({
          creditCards: [...state.creditCards, response.data!],
        }))
      }
    } catch (error) {
      console.error('Failed to add credit card:', error)
    }
  },

  updateCreditCard: async (id, data) => {
    try {
      await invoke('update_credit_card', { id, ...data })
      const newState = await get().loadVaultData()
      // Update selectedItem if it's the same card
      const updatedCard = newState.creditCards.find((c) => c.id === id)
      if (updatedCard && get().selectedItem && 'card_number' in get().selectedItem && get().selectedItem.id === id) {
        set({ selectedItem: updatedCard })
      }
    } catch (error) {
      console.error('Failed to update credit card:', error)
    }
  },

  deleteCreditCard: async (id) => {
    try {
      await invoke('delete_credit_card', { id })
      set((state) => ({
        creditCards: state.creditCards.filter((c) => c.id !== id),
        selectedItem:
          state.selectedItem && 'card_number' in state.selectedItem && state.selectedItem.id === id
            ? null
            : state.selectedItem,
      }))
    } catch (error) {
      console.error('Failed to delete credit card:', error)
    }
  },

  addFolder: async (name, vaultType = 'personal') => {
    try {
      const response = await invoke<{ success: boolean; data?: Folder }>(
        'create_folder',
        { name, vaultType }
      )
      if (response.success && response.data) {
        set((state) => ({
          folders: [...state.folders, response.data!],
        }))
      }
    } catch (error) {
      console.error('Failed to create folder:', error)
    }
  },

  updateFolder: async (id, name) => {
    try {
      await invoke('update_folder', { id, name })
      await get().loadVaultData()
    } catch (error) {
      console.error('Failed to update folder:', error)
    }
  },

  deleteFolder: async (id) => {
    try {
      await invoke('delete_folder', { id })
      set((state) => ({
        folders: state.folders.filter((f) => f.id !== id),
      }))
    } catch (error) {
      console.error('Failed to delete folder:', error)
    }
  },
}))
