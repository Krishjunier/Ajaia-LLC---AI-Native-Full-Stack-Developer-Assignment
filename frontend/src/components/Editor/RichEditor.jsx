import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Placeholder from '@tiptap/extension-placeholder'
import { useEffect, forwardRef, useImperativeHandle } from 'react'

const extensions = [
  StarterKit,
  Underline,
  TextAlign.configure({ types: ['heading', 'paragraph'] }),
  Placeholder.configure({ placeholder: 'Start writing your document…' }),
]

const EditorToolbar = ({ editor, readOnly }) => {
  if (!editor) return null

  const btn = (label, action, isActive, title) => (
    <button
      key={label}
      className={`toolbar-btn ${isActive ? 'active' : ''}`}
      onMouseDown={(e) => { e.preventDefault(); action() }}
      title={title || label}
      disabled={readOnly}
    >
      {label}
    </button>
  )

  return (
    <div className="editor-toolbar">
      {/* Heading selector */}
      <select
        className="toolbar-select"
        disabled={readOnly}
        value={
          editor.isActive('heading', { level: 1 }) ? '1'
            : editor.isActive('heading', { level: 2 }) ? '2'
            : editor.isActive('heading', { level: 3 }) ? '3'
            : '0'
        }
        onChange={(e) => {
          const lvl = parseInt(e.target.value)
          if (lvl === 0) editor.chain().focus().setParagraph().run()
          else editor.chain().focus().toggleHeading({ level: lvl }).run()
        }}
      >
        <option value="0">Paragraph</option>
        <option value="1">Heading 1</option>
        <option value="2">Heading 2</option>
        <option value="3">Heading 3</option>
      </select>

      <div className="toolbar-divider" />

      {btn('B', () => editor.chain().focus().toggleBold().run(),
        editor.isActive('bold'), 'Bold (Ctrl+B)')}
      {btn('I', () => editor.chain().focus().toggleItalic().run(),
        editor.isActive('italic'), 'Italic (Ctrl+I)')}
      {btn('U', () => editor.chain().focus().toggleUnderline().run(),
        editor.isActive('underline'), 'Underline (Ctrl+U)')}
      {btn('S̶', () => editor.chain().focus().toggleStrike().run(),
        editor.isActive('strike'), 'Strikethrough')}

      <div className="toolbar-divider" />

      {btn('≡L', () => editor.chain().focus().setTextAlign('left').run(),
        editor.isActive({ textAlign: 'left' }), 'Align Left')}
      {btn('≡C', () => editor.chain().focus().setTextAlign('center').run(),
        editor.isActive({ textAlign: 'center' }), 'Align Center')}
      {btn('≡R', () => editor.chain().focus().setTextAlign('right').run(),
        editor.isActive({ textAlign: 'right' }), 'Align Right')}

      <div className="toolbar-divider" />

      {btn('• List', () => editor.chain().focus().toggleBulletList().run(),
        editor.isActive('bulletList'), 'Bullet List')}
      {btn('1. List', () => editor.chain().focus().toggleOrderedList().run(),
        editor.isActive('orderedList'), 'Numbered List')}

      <div className="toolbar-divider" />

      {btn('" "', () => editor.chain().focus().toggleBlockquote().run(),
        editor.isActive('blockquote'), 'Blockquote')}
      {btn('<>', () => editor.chain().focus().toggleCode().run(),
        editor.isActive('code'), 'Inline Code')}

      <div className="toolbar-divider" />

      {btn('↩', () => editor.chain().focus().undo().run(), false, 'Undo')}
      {btn('↪', () => editor.chain().focus().redo().run(), false, 'Redo')}
    </div>
  )
}

const RichEditor = forwardRef(({ content, onChange, readOnly = false }, ref) => {
  const editor = useEditor({
    extensions,
    content,
    editable: !readOnly,
    onUpdate: ({ editor }) => {
      if (onChange) onChange(editor.getHTML())
    },
  })

  // Expose setContent via ref
  useImperativeHandle(ref, () => ({
    setContent: (html) => {
      if (editor) editor.commands.setContent(html)
    },
  }))

  // Update editable when readOnly changes
  useEffect(() => {
    if (editor) editor.setEditable(!readOnly)
  }, [editor, readOnly])

  // Update content when doc changes (sidebar nav)
  useEffect(() => {
    if (editor && content !== undefined && editor.getHTML() !== content) {
      editor.commands.setContent(content || '')
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content])

  return (
    <>
      <EditorToolbar editor={editor} readOnly={readOnly} />
      <div className="editor-scroll">
        <div className="editor-page">
          <EditorContent editor={editor} />
        </div>
      </div>
    </>
  )
})

RichEditor.displayName = 'RichEditor'
export default RichEditor
