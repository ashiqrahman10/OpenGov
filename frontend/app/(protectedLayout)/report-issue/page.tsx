import React from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from "@/components/ui/label"

const PublicFeedback = () => {
  return (
    <div className="max-w-lg  my-10 p-6 bg-white  rounded-md">
      <h1 className="text-2xl font-bold">Report an issue</h1>
      <p className="text-gray-600 mb-6">
        Submit your issues/thoughts on anything related to your government
      </p>
      <form>
        {/* <div className="mb-4">
          <Label htmlFor="name" className="block font-medium mb-1">
            Name
          </Label>
          <Input
            id="name"
            type="text"
            placeholder="Ben Dover"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-gray-500 text-sm">Your name is optional</p>
        </div> */}
        <div className="mb-6">
          <Label htmlFor="feedback" className="block font-medium mb-1">
            Issue
          </Label>
          <textarea
            id="feedback"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="I own a computer."
          />
          <p className="text-gray-500 text-sm">
            Please mention the project or initiative you're giving a feedback/issue on
          </p>
        </div>
        <Button
          type="submit"
          className="bg-black hover:bg-black text-white font-medium py-2 px-4 rounded-md"
        >
          Report Issue
        </Button>
      </form>
    </div>
  )
}

export default PublicFeedback