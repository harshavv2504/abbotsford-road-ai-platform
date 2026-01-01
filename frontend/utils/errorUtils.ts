export const handleApiError = (error: unknown): string => {
  console.error("API Error:", error);
  if (typeof error === 'object' && error !== null && 'message' in error) {
    try {
      // The error from the API is often a stringified JSON in the message property
      const errorDetails = JSON.parse((error as Error).message);
      if (errorDetails?.error?.code === 429) {
        return "Too many requests. Please wait a moment and try again.";
      }
      // Return a more specific error message if available
      return errorDetails?.error?.message || "An unexpected error occurred.";
    } catch (e) {
       // If parsing fails, it's likely not the JSON format we expect
       return (error as Error).message || "An unexpected error occurred.";
    }
  }
  return "An unexpected error occurred. Please try again later.";
};
