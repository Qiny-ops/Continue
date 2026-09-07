import { ref } from 'vue'
import { requirementApi } from '@/api/modules/requirement.js'

export function useRequirements() {
  const requirements = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  const fetchRequirements = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await requirementApi.getRequirements(params)
      requirements.value = response.results || response || []
      total.value = response.count || requirements.value.length
      return requirements.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createRequirement = async (data) => {
    loading.value = true
    try {
      const response = await requirementApi.createRequirement(data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateRequirement = async (id, data) => {
    try {
      const response = await requirementApi.updateRequirement(id, data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const deleteRequirement = async (id) => {
    try {
      await requirementApi.deleteRequirement(id)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const batchDeleteRequirements = async (ids) => {
    try {
      const response = await requirementApi.batchDeleteRequirements(ids)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const generateTestcases = async (id, data) => {
    try {
      const response = await requirementApi.generateTestcases(id, data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const batchGenerateTestcases = async (data) => {
    try {
      const response = await requirementApi.batchGenerateTestcases(data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  return {
    requirements,
    total,
    loading,
    error,
    fetchRequirements,
    createRequirement,
    updateRequirement,
    deleteRequirement,
    batchDeleteRequirements,
    generateTestcases,
    batchGenerateTestcases,
  }
}
